"""
real_world_check.py - compares the deployed crowd model with REAL observed crowd levels.

PRE-REGISTERED ANALYSIS (fixed before any observation is looked at; do not edit afterwards):
  Observer rubric (1-5): 1 almost empty, 2 quiet, 3 moderate, 4 busy, 5 very crowded.
  Observed level -> risk class: 1-2 Low, 3 Medium, 4-5 High.
  PRIMARY   : Spearman rho between the model crowd_score and the observed level, 95% bootstrap CI.
  SECONDARY : risk-class agreement (accuracy with Wilson 95% CI, balanced accuracy, majority-class
              baseline), the same metrics for the app's own heuristic baseline, and a per-category
              breakdown (only categories with n >= 8).
  The script refuses to compute metrics below --min-n (default 30) and never creates, edits or
  drops observations: invalid rows stop the run so you can fix them.

Usage:
  python real_world_check.py --self-test
  python real_world_check.py --csv LOG.csv --base-url http://localhost:5002
  python real_world_check.py --feedback-json data/feedback.json --base-url http://localhost:5002
CSV columns: site_id, visit_date (YYYY-MM-DD), observed_level (1-5); optional: visit_time, observer, notes.
"""
import argparse
import json
import os
import shutil
import sys
import urllib.parse
import urllib.request
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "master_dataset_fixed.csv")
OUT_DIR = os.path.join(ROOT, "outputs")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
CLASSES = ["Low", "Medium", "High"]


def level_to_class(v):
    if v <= 2:
        return "Low"
    if v == 3:
        return "Medium"
    return "High"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / float(n)
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return (float(c - h), float(c + h))


def spearman(a, b):
    ra = pd.Series(a).rank(method="average").values
    rb = pd.Series(b).rank(method="average").values
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def boot_ci(fn, n, n_boot=2000, seed=7):
    rng = np.random.RandomState(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.randint(0, n, n)
        v = fn(idx)
        if np.isfinite(v):
            vals.append(v)
    if len(vals) < n_boot // 2:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def fmt(x):
    return "n/a" if x is None or not np.isfinite(x) else "%.3f" % x


def self_test():
    lo, hi = wilson(24, 40)
    assert abs(lo - 0.446) < 0.002 and abs(hi - 0.737) < 0.002, (lo, hi)
    assert abs(spearman([1, 2, 3, 4, 5], [10, 20, 30, 40, 50]) - 1.0) < 1e-12
    assert abs(spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) + 1.0) < 1e-12
    ra = pd.Series([1, 1, 2]).rank(method="average").values
    assert list(ra) == [1.5, 1.5, 3.0]
    assert [level_to_class(v) for v in (1, 2, 3, 4, 5)] == ["Low", "Low", "Medium", "High", "High"]
    print("SELF-TEST PASSED (toy arrays only; no project data used or written)")


def backup_if_exists(path):
    if os.path.exists(path):
        b = path + ".bak_" + STAMP
        shutil.copy2(path, b)
        print("  (backed up existing %s -> %s)" % (os.path.basename(path), os.path.basename(b)))


def query(base, sid, date_str):
    url = base.rstrip("/") + "/model-comparison?" + urllib.parse.urlencode({"site_id": sid, "date": date_str})
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--csv")
    ap.add_argument("--feedback-json")
    ap.add_argument("--base-url")
    ap.add_argument("--min-n", type=int, default=30)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if bool(args.csv) == bool(args.feedback_json):
        sys.exit("Give exactly one of --csv or --feedback-json")
    if not args.base_url:
        sys.exit("--base-url is required (the running backend, e.g. http://localhost:5002)")
    src = args.csv or args.feedback_json
    if not os.path.exists(src):
        sys.exit("File not found: " + src)

    ds = pd.read_csv(DATA_PATH, usecols=["site_id", "site_name", "category"]).drop_duplicates("site_id")
    site_info = {}
    for r in ds.itertuples():
        site_info[int(r.site_id)] = (r.site_name, r.category)

    if args.csv:
        raw = pd.read_csv(src)
    else:
        with open(src, "r") as f:
            raw = pd.DataFrame(json.load(f))
        raw = raw.rename(columns={"date": "visit_date", "time": "visit_time", "actual_crowd_level": "observed_level"})
    missing = [c for c in ("site_id", "visit_date", "observed_level") if c not in raw.columns]
    if missing:
        sys.exit("Missing required columns: %s (found: %s)" % (missing, list(raw.columns)))
    if "visit_time" not in raw.columns:
        raw["visit_time"] = ""

    print("=" * 70)
    print("REAL-WORLD CHECK  (source: %s)" % src)
    print("=" * 70)
    print("  records in file: %d" % len(raw))

    today = pd.Timestamp(datetime.now().date())
    good, bad = [], []
    for i, r in raw.iterrows():
        problems = []
        try:
            sid = int(r["site_id"])
            if sid not in site_info:
                problems.append("site_id not in dataset")
        except Exception:
            sid = None
            problems.append("site_id not an integer")
        d = pd.to_datetime(r["visit_date"], errors="coerce")
        if pd.isna(d):
            problems.append("visit_date unreadable")
        elif d > today:
            problems.append("visit_date is in the future")
        try:
            lv = float(r["observed_level"])
            if lv != int(lv) or not (1 <= lv <= 5):
                problems.append("observed_level must be a whole number 1-5")
        except Exception:
            lv = None
            problems.append("observed_level missing or unreadable")
        if problems:
            bad.append((i + 1, "; ".join(problems)))
            continue
        vt = r["visit_time"]
        good.append({"site_id": sid, "visit_date": d.strftime("%Y-%m-%d"),
                     "visit_time": "" if pd.isna(vt) else str(vt),
                     "observed_level": int(lv),
                     "site_name": site_info[sid][0], "category": site_info[sid][1]})
    if bad:
        print("  STOP: %d invalid record(s). Nothing was changed; fix or remove them in your log and re-run:" % len(bad))
        for rec, why in bad[:40]:
            print("    record %d: %s" % (rec, why))
        sys.exit(4)

    obs_df = pd.DataFrame(good)
    before = len(obs_df)
    obs_df = obs_df.drop_duplicates(["site_id", "visit_date", "visit_time"]).reset_index(drop=True)
    if before != len(obs_df):
        print("  duplicate (site, date, time) records ignored: %d" % (before - len(obs_df)))
    n = len(obs_df)
    print("  valid observations: %d" % n)
    if n == 0:
        print("INSUFFICIENT DATA: no valid observations. No metrics computed.")
        return

    obs_df["weekend"] = pd.to_datetime(obs_df["visit_date"]).dt.dayofweek >= 5
    print("  by category: %s" % obs_df["category"].value_counts().to_dict())
    print("  weekend rows %d | weekday rows %d | distinct sites %d | months covered %s" % (
        int(obs_df["weekend"].sum()), int((~obs_df["weekend"]).sum()), obs_df["site_id"].nunique(),
        sorted(set(pd.to_datetime(obs_df["visit_date"]).dt.month.tolist()))))
    print("  observed level counts: %s" % obs_df["observed_level"].value_counts().sort_index().to_dict())
    if obs_df["category"].value_counts(normalize=True).iloc[0] > 0.6:
        print("  WARNING: more than 60%% of observations come from one category; results describe that category.")
    if n < args.min_n:
        print("INSUFFICIENT DATA: %d valid observations < minimum %d. No metrics computed." % (n, args.min_n))
        return
    exploratory = args.min_n < 30
    if exploratory:
        print("  NOTE: --min-n below 30, so everything below is EXPLORATORY only.")

    rf_s, hb_s, rf_c, hb_c, failures = [], [], [], [], []
    for r in obs_df.itertuples():
        try:
            d = query(args.base_url, r.site_id, r.visit_date)
            rf, hb = d.get("random_forest"), d.get("heuristic_baseline")
            if not rf or not hb:
                failures.append((r.site_id, r.visit_date, "no random_forest/heuristic in response: %s" % d))
                continue
            rf_s.append(float(rf["crowd_score"]))
            rf_c.append(str(rf["risk_level"]))
            hb_s.append(float(hb["crowd_score"]))
            hb_c.append(str(hb["risk_level"]))
        except Exception as e:
            failures.append((r.site_id, r.visit_date, repr(e)))
    if failures:
        print("  STOP: could not get predictions for %d observation(s) (is the backend running at %s?):" % (
            len(failures), args.base_url))
        for f_ in failures[:20]:
            print("    site %s on %s: %s" % f_)
        sys.exit(5)

    obs = obs_df["observed_level"].values.astype(float)
    rf_s, hb_s = np.array(rf_s), np.array(hb_s)
    obs_c = [level_to_class(v) for v in obs]

    rho_rf = spearman(rf_s, obs)
    ci_rf = boot_ci(lambda i: spearman(rf_s[i], obs[i]), n)
    rho_hb = spearman(hb_s, obs)
    ci_hb = boot_ci(lambda i: spearman(hb_s[i], obs[i]), n)
    ci_diff = boot_ci(lambda i: spearman(rf_s[i], obs[i]) - spearman(hb_s[i], obs[i]), n)

    print("")
    print("PRIMARY: Spearman rho, model crowd_score vs observed level (n=%d)" % n)
    print("  random forest : rho %s   95%% bootstrap CI [%s, %s]" % (fmt(rho_rf), fmt(ci_rf[0]), fmt(ci_rf[1])))
    print("  app heuristic : rho %s   95%% bootstrap CI [%s, %s]" % (fmt(rho_hb), fmt(ci_hb[0]), fmt(ci_hb[1])))
    print("  paired difference (RF - heuristic) 95%% CI [%s, %s]" % (fmt(ci_diff[0]), fmt(ci_diff[1])))

    print("")
    print("SECONDARY: risk-class agreement (observed 1-2 Low, 3 Medium, 4-5 High)")
    results = {"n": n, "exploratory": exploratory, "rho_rf": rho_rf, "rho_rf_ci": ci_rf,
               "rho_heuristic": rho_hb, "rho_heuristic_ci": ci_hb, "rho_diff_ci": ci_diff}
    maj_class = max(set(obs_c), key=obs_c.count)
    maj_acc = obs_c.count(maj_class) / float(n)
    for label, pc in (("random forest", rf_c), ("app heuristic", hb_c)):
        k = sum(1 for a, b in zip(obs_c, pc) if a == b)
        lo, hi = wilson(k, n)
        bal = float(balanced_accuracy_score(obs_c, pc))
        print("  %-14s accuracy %.3f (95%% Wilson CI [%.3f, %.3f]) | balanced accuracy %.3f" % (label, k / float(n), lo, hi, bal))
        results[label.replace(" ", "_") + "_class"] = {"accuracy": k / float(n), "wilson_ci": [lo, hi], "balanced_accuracy": bal}
    print("  majority-class baseline (always '%s'): accuracy %.3f" % (maj_class, maj_acc))
    cm = pd.DataFrame(confusion_matrix(obs_c, rf_c, labels=CLASSES),
                      index=["obs_" + c for c in CLASSES], columns=["pred_" + c for c in CLASSES])
    print("  random forest confusion matrix (rows observed, columns predicted):")
    print(cm.to_string())
    tmp = pd.DataFrame({"obs": obs, "pred_class": rf_c})
    print("  mean observed level by RF predicted class:")
    print(tmp.groupby("pred_class")["obs"].agg(["count", "mean"]).round(2).to_string())

    print("")
    print("PER CATEGORY (Spearman only when n >= 8)")
    per_cat = {}
    for cat, g in obs_df.groupby("category"):
        idx = g.index.values
        if len(idx) >= 8:
            rho = spearman(rf_s[idx], obs[idx])
            per_cat[cat] = {"n": int(len(idx)), "rho": rho}
            print("  %-10s n=%d  rho %s" % (cat, len(idx), fmt(rho)))
        else:
            per_cat[cat] = {"n": int(len(idx)), "rho": None}
            print("  %-10s n=%d  (below 8, not computed)" % (cat, len(idx)))
    results["per_category"] = per_cat

    print("")
    print("PRE-REGISTERED VERDICT")
    if not np.isfinite(ci_rf[0]):
        v1 = "undetermined (observed levels or predictions are constant, or too few distinct values)"
    elif ci_rf[0] > 0:
        v1 = "the model ranks real crowd levels better than chance (95%% CI above 0, n=%d)" % n
    else:
        v1 = "cannot be distinguished from chance at this sample size (95%% CI reaches 0 or below, n=%d)" % n
    if not np.isfinite(ci_diff[0]):
        v2 = "RF vs heuristic: undetermined"
    elif ci_diff[0] > 0:
        v2 = "RF ranks better than the app's heuristic baseline"
    elif ci_diff[1] < 0:
        v2 = "RF ranks WORSE than the app's heuristic baseline"
    else:
        v2 = "RF and the app's heuristic baseline are not distinguishable"
    print("  PRIMARY  : " + v1)
    print("  COMPARE  : " + v2)
    print("  Report the interval, not just rho. Observations are self-reported and cover only the sites,")
    print("  dates and observers in your log; this does not validate the synthetic target elsewhere.")
    results["verdict"] = {"primary": v1, "vs_heuristic": v2}

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "real_world_check.json")
    backup_if_exists(out)
    results["generated"] = datetime.now().isoformat()
    results["source"] = src
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("  wrote %s" % out)


if __name__ == "__main__":
    main()
