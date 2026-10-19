"""
validate_model.py - independent validation of the crowd-score Random Forest.

READ-ONLY with respect to the models and data folders (it never unpickles a model).
Writes only to the outputs folder; any existing output file is backed up first.

Every metric is labelled with its split. Nothing here changes the locked
headline numbers; the tuning section is a sensitivity analysis, not selection.

Usage:
  python validate_model.py [--skip-tuning] [--skip-ablation] [--allow-mismatch] [--repeats 3]
"""
import argparse
import json
import os
import platform
import shutil
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             mean_absolute_error, r2_score)
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "master_dataset_fixed.csv")
MODELS_DIR = os.path.join(ROOT, "models")
OUT_DIR = os.path.join(ROOT, "outputs")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
T0 = time.time()

NUMERIC = [
    "day_of_week", "month", "is_weekend", "is_public_holiday", "is_festival_period",
    "avg_temperature_c", "avg_rainfall_mm", "daily_flights_at_cmb", "hotel_occupancy_rate",
    "capacity_per_day", "is_eco_friendly", "is_unesco", "entrance_fee_lkr",
]
CATEGORICAL = ["category", "season", "district"]
FEATS = NUMERIC + CATEGORICAL
HOLDOUT_NAMES = [
    "Bentota Beach", "Bundala National Park", "Colombo Lotus Tower",
    "Kalpitiya Beach", "Kande Viharaya", "Kandy Lake",
    "Minneriya National Park", "Pasikuda Beach", "Tangalle Beach",
    "Wilpattu National Park",
]
EXPECTED_ROWS = 144007
EXPECTED_SITES = 197
DEFAULT_PARAMS = {"n_estimators": 50, "max_depth": 12, "min_samples_split": 7}
LOCKED = {"mae": 0.1232, "r2": 0.3331, "acc": 0.7731, "bacc": 0.5754, "base_mae": 0.2835}
LOCKED_RANDOM = {"mae": 0.0679, "r2": 0.8492}
LOCKED_CV = {"mae": 0.0694, "r2": 0.8194, "r2_std": 0.0218}

S_HOLD = "site-holdout (10 fixed sites)"
S_GCV = "site-grouped CV (197 sites)"
S_RAND = "random 80/20 split"
S_TEMP = "temporal 2024->2025 (same sites)"
S_TEMP_HOLD = "temporal + unseen sites (10 fixed)"
S_TEMP_GCV = "temporal + unseen sites (grouped CV)"
S_KF = "unshuffled 5-fold (file order)"
S_ABL_H = "ablation, site-holdout"
S_ABL_G = "ablation, site-grouped CV (repeat 0)"
S_TUNE = "tuning check, site-holdout"
CORE = [S_HOLD, S_GCV, S_RAND, S_TEMP, S_TEMP_HOLD, S_TEMP_GCV, S_KF]

ROWS = []
RESULTS = {"errors": []}

CHAINS = {
    "category_mean": [["category"]],
    "category_month_mean": [["category", "month"], ["category"]],
    "site_mean": [["site_id"]],
    "site_month_mean": [["site_id", "month"], ["site_id"]],
}


def hdr(title):
    print("")
    print("=" * 72)
    print("%s   [t+%.0fs]" % (title, time.time() - T0))
    print("=" * 72)
    sys.stdout.flush()


def score(y, p):
    return {"mae": float(mean_absolute_error(y, p)), "r2": float(r2_score(y, p))}


def add_row(split, model, fold, y, p):
    d = {"split": split, "model": model, "fold": str(fold), "n_test": int(len(y))}
    d.update(score(y, p))
    ROWS.append(d)
    return d


def make_pre(num, cat, scale=False):
    steps = []
    if num:
        steps.append(("num", StandardScaler() if scale else "passthrough", list(num)))
    if cat:
        steps.append(("cat", OneHotEncoder(handle_unknown="ignore"), list(cat)))
    return ColumnTransformer(steps)


def make_model(name, params, num, cat, seed=42):
    if name == "rf":
        return Pipeline([("pre", make_pre(num, cat)),
                         ("model", RandomForestRegressor(random_state=seed, n_jobs=-1, **params))])
    if name == "ridge":
        return Pipeline([("pre", make_pre(num, cat, scale=True)),
                         ("model", Ridge(alpha=1.0))])
    raise ValueError("unknown model " + name)


def grp_pred(tr, te, chain):
    pred = pd.Series(np.nan, index=te.index)
    for keys in chain:
        m = tr.groupby(keys)["y"].mean().rename("_p").reset_index()
        merged = te[keys].merge(m, on=keys, how="left")
        merged.index = te.index
        pred = pred.fillna(merged["_p"])
    return pred.fillna(tr["y"].mean()).values


def run_models(tr, te, names, params, num=None, cat=None, seed=42):
    num = NUMERIC if num is None else num
    cat = CATEGORICAL if cat is None else cat
    cols = list(num) + list(cat)
    out = {}
    for n in names:
        if n == "mean":
            p = np.full(len(te), tr["y"].mean())
        elif n in CHAINS:
            p = grp_pred(tr, te, CHAINS[n])
        else:
            m = make_model(n, params, num, cat, seed)
            m.fit(tr[cols], tr["y"])
            p = m.predict(te[cols])
        out[n] = np.clip(np.asarray(p, dtype=float), 0.0, 1.0)
    return out


def site_folds(site_ids, n_splits, seed):
    rng = np.random.RandomState(seed)
    s = np.array(sorted(site_ids))
    rng.shuffle(s)
    return [set(x.tolist()) for x in np.array_split(s, n_splits)]


def table(split):
    d = pd.DataFrame([r for r in ROWS if r["split"] == split])
    if d.empty:
        print("  (no rows)")
        return
    order = list(dict.fromkeys(d["model"]))
    g = d.groupby("model")
    t = pd.DataFrame({
        "folds": g.size(),
        "MAE": g["mae"].mean(), "MAE_sd": g["mae"].std(),
        "R2": g["r2"].mean(), "R2_sd": g["r2"].std(),
        "R2_min": g["r2"].min(), "R2_max": g["r2"].max(),
    }).loc[order]
    print(t.round(4).to_string())
    sys.stdout.flush()


def build_summary():
    d = pd.DataFrame(ROWS)
    out = []
    for (split, model), g in d.groupby(["split", "model"], sort=False):
        n = len(g)
        out.append({
            "split": split, "model": model, "n_folds": n,
            "mae_mean": g["mae"].mean(), "mae_sd": g["mae"].std() if n > 1 else np.nan,
            "r2_mean": g["r2"].mean(), "r2_sd": g["r2"].std() if n > 1 else np.nan,
            "r2_min": g["r2"].min(), "r2_max": g["r2"].max(),
        })
    return pd.DataFrame(out)


def snapshot():
    snap = {}
    for name in sorted(os.listdir(MODELS_DIR)):
        p = os.path.join(MODELS_DIR, name)
        if os.path.isfile(p):
            st = os.stat(p)
            snap[p] = (st.st_size, st.st_mtime_ns)
    st = os.stat(DATA_PATH)
    snap[DATA_PATH] = (st.st_size, st.st_mtime_ns)
    return snap


def backup_if_exists(path):
    if os.path.exists(path):
        b = path + ".bak_" + STAMP
        shutil.copy2(path, b)
        print("  (backed up existing %s -> %s)" % (os.path.basename(path), os.path.basename(b)))


def jdefault(o):
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def plot_r2(summ, path):
    splits = [s for s in CORE if (summ["split"] == s).any()]
    models = ["mean", "category_month_mean", "ridge", "rf"]
    x = np.arange(len(splits))
    w = 0.2
    fig, ax = plt.subplots(figsize=(13, 5.5))
    for i, m in enumerate(models):
        vals, errs = [], []
        for s in splits:
            r = summ[(summ["split"] == s) & (summ["model"] == m)]
            if len(r):
                vals.append(float(r["r2_mean"].iloc[0]))
                sd = r["r2_sd"].iloc[0]
                errs.append(0.0 if pd.isna(sd) else float(sd))
            else:
                vals.append(np.nan)
                errs.append(0.0)
        pos = x + (i - 1.5) * w
        ax.bar(pos, np.nan_to_num(vals), w, yerr=errs, label=m, capsize=2)
        for xp, v in zip(pos, vals):
            if np.isfinite(v):
                ax.text(xp, v + 0.02 if v >= 0 else v - 0.07, "%.2f" % v, ha="center", fontsize=7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace(" (", "\n(") for s in splits], fontsize=8)
    ax.set_ylabel("R2 (mean across folds; bars = +/- 1 sd)")
    ax.set_title("Crowd-score R2 by validation scheme (synthetic target)")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-tuning", action="store_true")
    ap.add_argument("--skip-ablation", action="store_true")
    ap.add_argument("--allow-mismatch", action="store_true")
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()

    if not os.path.exists(DATA_PATH):
        print("STOP: dataset not found: " + DATA_PATH)
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)
    snap_before = snapshot()

    # ------------------------------------------------------------------ 0
    hdr("SECTION 0 - ENVIRONMENT AND DATA CHECKS")
    print("  python %s | sklearn %s | pandas %s | numpy %s" % (
        platform.python_version(), sklearn.__version__, pd.__version__, np.__version__))
    meta = {}
    mp = os.path.join(MODELS_DIR, "model_metadata.json")
    if os.path.exists(mp):
        with open(mp, "r") as f:
            meta = json.load(f)
    params = dict(DEFAULT_PARAMS)
    if meta.get("best_hyperparameters"):
        params = {k: int(v) for k, v in meta["best_hyperparameters"].items()}
    print("  hyperparameters used (from model_metadata.json): %s" % params)
    if meta.get("sklearn_version") and meta["sklearn_version"] != sklearn.__version__:
        print("  NOTE: models were trained with sklearn %s, this run uses %s "
              "(tiny numeric differences are possible)" % (meta["sklearn_version"], sklearn.__version__))

    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["y"] = df["crowd_score_normalized"]
    keep = ["date", "year", "site_id", "site_name", "risk_level", "y"] + NUMERIC + CATEGORICAL
    df = df[list(dict.fromkeys(keep))].reset_index(drop=True)

    problems = []
    if len(df) != EXPECTED_ROWS:
        problems.append("rows %d != %d" % (len(df), EXPECTED_ROWS))
    if df["site_id"].nunique() != EXPECTED_SITES:
        problems.append("sites %d != %d" % (df["site_id"].nunique(), EXPECTED_SITES))
    if sorted(df["year"].unique().tolist()) != [2024, 2025]:
        problems.append("years are %s, expected [2024, 2025]" % sorted(df["year"].unique().tolist()))
    if df.duplicated(["site_id", "date"]).any():
        problems.append("duplicate (site_id, date) rows")
    if df[FEATS + ["y", "risk_level"]].isna().any().any():
        problems.append("NaN values in used columns")
    holdout_sites = set(df.loc[df["site_name"].isin(HOLDOUT_NAMES), "site_id"].unique().tolist())
    if len(holdout_sites) != len(HOLDOUT_NAMES):
        problems.append("holdout site names resolve to %d site_ids, expected %d" % (
            len(holdout_sites), len(HOLDOUT_NAMES)))
    if problems:
        print("  STOP: " + "; ".join(problems))
        sys.exit(1)

    print("  rows %d | sites %d | dates %s .. %s" % (
        len(df), df["site_id"].nunique(), df["date"].min().date(), df["date"].max().date()))
    print("  rows per year: %s" % df["year"].value_counts().sort_index().to_dict())
    print("  target y: mean %.4f sd %.4f | share at 1.0: %.3f | share at 0.0: %.3f" % (
        df["y"].mean(), df["y"].std(), (df["y"] >= 1.0).mean(), (df["y"] <= 0.0).mean()))
    print("  mean y by year: %s" % df.groupby("year")["y"].mean().round(4).to_dict())
    date_sorted = bool(df["date"].is_monotonic_increasing)
    site_sorted = bool(df["site_id"].is_monotonic_increasing)
    if date_sorted:
        order = "DATE-major (sorted by date, then site)"
    elif site_sorted:
        order = "SITE-major (sorted by site, then date)"
    else:
        order = "neither date- nor site-sorted"
    print("  file order: %s" % order)
    RESULTS["data"] = {"rows": len(df), "sites": int(df["site_id"].nunique()), "file_order": order,
                       "params": params, "sklearn": sklearn.__version__}

    hmask = df["site_id"].isin(holdout_sites).values
    tr_h, te_h = df[~hmask], df[hmask]
    names_main = ["mean", "category_mean", "category_month_mean", "ridge", "rf"]

    # ------------------------------------------------------------------ 1
    hdr("SECTION 1 - REPRODUCE THE LOCKED SITE-HOLDOUT NUMBERS (gate)")
    preds = run_models(tr_h, te_h, names_main, params)
    for n in names_main:
        add_row(S_HOLD, n, 0, te_h["y"].values, preds[n])
    got = score(te_h["y"].values, preds["rf"])
    base = score(te_h["y"].values, preds["mean"])
    le = LabelEncoder()
    yr = le.fit_transform(df["risk_level"])
    clf = Pipeline([("pre", make_pre(NUMERIC, CATEGORICAL)),
                    ("model", RandomForestClassifier(random_state=42, n_jobs=-1,
                                                     class_weight="balanced", **params))])
    clf.fit(tr_h[FEATS], yr[~hmask])
    pr = clf.predict(te_h[FEATS])
    acc = float(accuracy_score(yr[hmask], pr))
    bacc = float(balanced_accuracy_score(yr[hmask], pr))
    checks = [
        ("regression MAE (site-holdout)", round(got["mae"], 4), LOCKED["mae"], True),
        ("regression R2  (site-holdout)", round(got["r2"], 4), LOCKED["r2"], True),
        ("mean-predictor MAE (site-holdout)", round(base["mae"], 4), LOCKED["base_mae"], False),
        ("classifier accuracy (site-holdout)", round(acc, 4), LOCKED["acc"], False),
        ("classifier balanced acc (site-holdout)", round(bacc, 4), LOCKED["bacc"], False),
    ]
    gate_ok = True
    for label, g_, l_, gating in checks:
        ok = abs(g_ - l_) < 1e-9
        if gating and not ok:
            gate_ok = False
        print("  %-42s got %.4f  locked %.4f  %s%s" % (
            label, g_, l_, "MATCH" if ok else "DIFFERENT", "  (gating)" if gating else ""))
    print("  mean-predictor R2 on the 10 holdout sites (new, split = site-holdout): %.4f" % base["r2"])
    RESULTS["reproduction"] = {"got": got, "baseline": base, "acc": acc, "bacc": bacc, "gate_ok": gate_ok}
    if not gate_ok and not args.allow_mismatch:
        print("")
        print("  STOP: the locked MAE/R2 were NOT reproduced. Do not use any number from this run.")
        print("  Paste this section back to the assistant. Likely causes: different sklearn version,")
        print("  different data file, or different hyperparameters. Re-run with --allow-mismatch")
        print("  only to diagnose, never to report.")
        sys.exit(2)
    if gate_ok:
        print("  GATE PASSED: locked site-holdout MAE and R2 reproduced exactly.")

    # ------------------------------------------------------------------ 1b
    hdr("SECTION 1b - WHAT THE LOCKED 5-FOLD CV ACTUALLY MEASURED (unshuffled KFold, file order)")
    kf_r2, kf_mae = [], []
    for k, (tri, tei) in enumerate(KFold(n_splits=5).split(df)):
        tr, te = df.iloc[tri], df.iloc[tei]
        unseen = len(set(te["site_id"]) - set(tr["site_id"]))
        m = make_model("rf", params, NUMERIC, CATEGORICAL)
        m.fit(tr[FEATS], tr["y"])
        p = np.clip(m.predict(te[FEATS]), 0, 1)
        d = add_row(S_KF, "rf", "f%d" % k, te["y"].values, p)
        kf_r2.append(d["r2"])
        kf_mae.append(d["mae"])
        print("  fold %d: test dates %s..%s | test sites %d | test sites unseen in train %d | MAE %.4f R2 %.4f" % (
            k, te["date"].min().date(), te["date"].max().date(), te["site_id"].nunique(),
            unseen, d["mae"], d["r2"]))
    print("  CV R2 %.4f +/- %.4f (locked %.4f +/- %.4f) | CV MAE %.4f (locked %.4f)" % (
        np.mean(kf_r2), np.std(kf_r2), LOCKED_CV["r2"], LOCKED_CV["r2_std"],
        np.mean(kf_mae), LOCKED_CV["mae"]))

    # ------------------------------------------------------------------ 2
    hdr("SECTION 2 - SITE-GROUPED CV OVER ALL %d SITES (5 folds x %d repeats)" % (EXPECTED_SITES, args.repeats))
    all_sites = sorted(df["site_id"].unique().tolist())
    oof = {"rf": np.full(len(df), np.nan), "category_month_mean": np.full(len(df), np.nan)}
    for r in range(args.repeats):
        folds = site_folds(all_sites, 5, 1000 + r)
        for k, fs in enumerate(folds):
            m = df["site_id"].isin(fs).values
            tr, te = df[~m], df[m]
            p = run_models(tr, te, names_main, params)
            for n in names_main:
                add_row(S_GCV, n, "r%d-f%d" % (r, k), te["y"].values, p[n])
            if r == 0:
                for n in oof:
                    oof[n][m] = p[n]
        print("  repeat %d done" % r)
        sys.stdout.flush()
    rf_rows = [x for x in ROWS if x["split"] == S_GCV and x["model"] == "rf"]
    cm_rows = [x for x in ROWS if x["split"] == S_GCV and x["model"] == "category_month_mean"]
    print("  RF R2 per fold            : " + " ".join("%.3f" % x["r2"] for x in rf_rows))
    print("  category_month_mean R2    : " + " ".join("%.3f" % x["r2"] for x in cm_rows))
    table(S_GCV)

    # ------------------------------------------------------------------ 3
    hdr("SECTION 3 - RANDOM 80/20 SPLIT (reference only; same sites in train and test)")
    names_seen = ["mean", "category_mean", "category_month_mean", "site_mean", "site_month_mean", "ridge", "rf"]
    tr, te = train_test_split(df, test_size=0.2, random_state=42)
    p = run_models(tr, te, names_seen, params)
    for n in names_seen:
        add_row(S_RAND, n, 0, te["y"].values, p[n])
    table(S_RAND)
    rr = score(te["y"].values, p["rf"])
    print("  RF vs locked random-split: MAE %.4f (locked %.4f) R2 %.4f (locked %.4f)" % (
        rr["mae"], LOCKED_RANDOM["mae"], rr["r2"], LOCKED_RANDOM["r2"]))

    # ------------------------------------------------------------------ 4
    hdr("SECTION 4 - TEMPORAL VALIDATION (train 2024 -> test 2025)")
    y24 = df[df["year"] == 2024]
    y25 = df[df["year"] == 2025]
    s24 = y24.groupby("site_id")["y"].mean()
    s25 = y25.groupby("site_id")["y"].mean()
    print("  correlation of per-site mean y, 2024 vs 2025: %.4f" % np.corrcoef(s24.values, s25.reindex(s24.index).values)[0, 1])
    print("  4a. same sites, unseen year")
    p = run_models(y24, y25, names_seen, params)
    for n in names_seen:
        add_row(S_TEMP, n, 0, y25["y"].values, p[n])
    table(S_TEMP)
    print("  4b. unseen sites AND unseen year (10 fixed holdout sites)")
    trt = y24[~y24["site_id"].isin(holdout_sites)]
    tet = y25[y25["site_id"].isin(holdout_sites)]
    p = run_models(trt, tet, names_main, params)
    for n in names_main:
        add_row(S_TEMP_HOLD, n, 0, tet["y"].values, p[n])
    table(S_TEMP_HOLD)
    print("  4c. unseen sites AND unseen year (site-grouped 5-fold, repeat 0 split)")
    folds0 = site_folds(all_sites, 5, 1000)
    for k, fs in enumerate(folds0):
        trt = y24[~y24["site_id"].isin(fs)]
        tet = y25[y25["site_id"].isin(fs)]
        p = run_models(trt, tet, names_main, params)
        for n in names_main:
            add_row(S_TEMP_GCV, n, "f%d" % k, tet["y"].values, p[n])
    table(S_TEMP_GCV)

    # ------------------------------------------------------------------ 5
    if not args.skip_ablation:
        try:
            hdr("SECTION 5 - LEAKAGE ABLATION AND SHUFFLED-TARGET SANITY CHECK (RF only)")
            variants = [
                ("full (reference)", []),
                ("drop occupancy+flights", ["hotel_occupancy_rate", "daily_flights_at_cmb"]),
                ("drop capacity_per_day", ["capacity_per_day"]),
                ("drop is_weekend+is_public_holiday", ["is_weekend", "is_public_holiday"]),
                ("drop season", ["season"]),
                ("drop ALL of the above", ["hotel_occupancy_rate", "daily_flights_at_cmb", "capacity_per_day",
                                           "is_weekend", "is_public_holiday", "season"]),
            ]
            for label, drop in variants:
                num = [f for f in NUMERIC if f not in drop]
                cat = [f for f in CATEGORICAL if f not in drop]
                p = run_models(tr_h, te_h, ["rf"], params, num, cat)
                add_row(S_ABL_H, label, 0, te_h["y"].values, p["rf"])
                for k, fs in enumerate(folds0):
                    m = df["site_id"].isin(fs).values
                    p = run_models(df[~m], df[m], ["rf"], params, num, cat)
                    add_row(S_ABL_G, label, "f%d" % k, df[m]["y"].values, p["rf"])
                print("  done: %s" % label)
                sys.stdout.flush()
            rng = np.random.RandomState(2026)
            trs = tr_h.copy()
            trs["y"] = rng.permutation(trs["y"].values)
            p = run_models(trs, te_h, ["rf"], params)
            add_row(S_ABL_H, "shuffled-target RF", 0, te_h["y"].values, p["rf"])
            for k, fs in enumerate(folds0):
                m = df["site_id"].isin(fs).values
                trs = df[~m].copy()
                trs["y"] = rng.permutation(trs["y"].values)
                p = run_models(trs, df[m], ["rf"], params)
                add_row(S_ABL_G, "shuffled-target RF", "f%d" % k, df[m]["y"].values, p["rf"])
            print("  --- " + S_ABL_H)
            table(S_ABL_H)
            print("  --- " + S_ABL_G)
            table(S_ABL_G)
            print("  (shuffled-target R2 should be ~0 or slightly negative; clearly positive would mean a pipeline leak)")
        except Exception as e:
            RESULTS["errors"].append("ablation: %r" % (e,))
            print("  WARNING: ablation failed: %r" % (e,))

    # ------------------------------------------------------------------ 6
    if not args.skip_tuning:
        try:
            hdr("SECTION 6 - LEAKAGE-FREE TUNING CHECK (site-grouped inner CV on the 187 training sites)")
            print("  27 combinations x 3 inner folds = 81 fits; this is the slow section.")
            print("  Holdout sites are NOT used for selection; they are scored once at the end.")
            pool = df[~hmask].reset_index(drop=True)
            inner = site_folds(sorted(pool["site_id"].unique().tolist()), 3, 7)
            inner_masks = [pool["site_id"].isin(fs).values for fs in inner]
            grid_rows = []
            for ne in (50, 100, 150):
                for md in (8, 10, 12):
                    for ms in (3, 5, 7):
                        prm = {"n_estimators": ne, "max_depth": md, "min_samples_split": ms}
                        maes, r2s = [], []
                        for m in inner_masks:
                            p = run_models(pool[~m], pool[m], ["rf"], prm)["rf"]
                            s = score(pool[m]["y"].values, p)
                            maes.append(s["mae"])
                            r2s.append(s["r2"])
                        row = dict(prm)
                        row["cv_mae"] = float(np.mean(maes))
                        row["cv_r2"] = float(np.mean(r2s))
                        grid_rows.append(row)
                        print("  n=%3d depth=%2d split=%d  grouped-CV MAE %.4f R2 %.4f" % (
                            ne, md, ms, row["cv_mae"], row["cv_r2"]))
                        sys.stdout.flush()
            g = pd.DataFrame(grid_rows).sort_values("cv_mae").reset_index(drop=True)
            print("  top 5 by site-grouped CV MAE:")
            print(g.head(5).round(4).to_string(index=False))
            orig = g[(g["n_estimators"] == params["n_estimators"]) & (g["max_depth"] == params["max_depth"])
                     & (g["min_samples_split"] == params["min_samples_split"])]
            if len(orig):
                print("  original params %s rank under site-grouped CV: %d of %d" % (
                    params, int(orig.index[0]) + 1, len(g)))
            best = g.iloc[0]
            bp = {"n_estimators": int(best["n_estimators"]), "max_depth": int(best["max_depth"]),
                  "min_samples_split": int(best["min_samples_split"])}
            p = run_models(tr_h, te_h, ["rf"], bp)["rf"]
            d = add_row(S_TUNE, "rf_tuned_site_grouped " + str(bp), 0, te_h["y"].values, p)
            print("  leakage-free best params: %s" % bp)
            print("  site-holdout (scored once): MAE %.4f R2 %.4f | original params: MAE %.4f R2 %.4f" % (
                d["mae"], d["r2"], got["mae"], got["r2"]))
            print("  SENSITIVITY ANALYSIS ONLY: do not swap parameters because this number is higher.")
            RESULTS["tuning"] = {"grid": g.to_dict("records"), "best": bp, "holdout": d}
        except Exception as e:
            RESULTS["errors"].append("tuning: %r" % (e,))
            print("  WARNING: tuning check failed: %r" % (e,))

    # ------------------------------------------------------------------ 7
    hdr("SECTION 7 - ERROR ANALYSIS (out-of-fold predictions, site-grouped CV repeat 0) AND OUTPUT FILES")
    pool = df[["site_id", "site_name", "category", "y"]].copy()
    pool["p_rf"] = oof["rf"]
    pool["p_cm"] = oof["category_month_mean"]
    pool["abs_rf"] = (pool["y"] - pool["p_rf"]).abs()
    pool["abs_cm"] = (pool["y"] - pool["p_cm"]).abs()
    pool["err_rf"] = pool["p_rf"] - pool["y"]

    site_rows = []
    for (sid, sname, cat), g in pool.groupby(["site_id", "site_name", "category"], sort=True):
        site_rows.append({
            "site_id": sid, "site_name": sname, "category": cat, "n": len(g),
            "actual_mean": g["y"].mean(), "pred_mean": g["p_rf"].mean(), "bias": g["err_rf"].mean(),
            "mae_rf": g["abs_rf"].mean(), "mae_category_month_mean": g["abs_cm"].mean(),
            "r2_within_site": r2_score(g["y"], g["p_rf"]) if g["y"].var() > 0 else np.nan,
            "in_fixed_holdout": sid in holdout_sites,
        })
    per_site = pd.DataFrame(site_rows)

    cat_rows = []
    for cat, g in pool.groupby("category", sort=True):
        cat_rows.append({
            "category": cat, "n_sites": int(g["site_id"].nunique()), "n_rows": len(g),
            "mae_rf": g["abs_rf"].mean(), "mae_category_month_mean": g["abs_cm"].mean(),
            "bias": g["err_rf"].mean(), "r2_pooled": r2_score(g["y"], g["p_rf"]),
            "n_fixed_holdout_sites": int(per_site[(per_site["category"] == cat) & per_site["in_fixed_holdout"]].shape[0]),
        })
    per_cat = pd.DataFrame(cat_rows)

    print("  per category (RF out-of-fold, unseen sites):")
    print(per_cat.round(4).to_string(index=False))
    srt = per_site.sort_values("mae_rf")
    print("  5 best sites by MAE:")
    print(srt.head(5)[["site_name", "category", "mae_rf", "bias"]].round(4).to_string(index=False))
    print("  10 worst sites by MAE:")
    print(srt.tail(10)[["site_name", "category", "mae_rf", "bias"]].round(4).to_string(index=False))
    hs = per_site[per_site["in_fixed_holdout"]]
    print("  mean per-site MAE: all 197 sites %.4f | the 10 fixed holdout sites %.4f" % (
        per_site["mae_rf"].mean(), hs["mae_rf"].mean()))
    print("  sites where RF MAE is worse than category_month_mean: %d of %d" % (
        int((per_site["mae_rf"] > per_site["mae_category_month_mean"]).sum()), len(per_site)))

    pool["bin"] = pd.qcut(pool["p_rf"].rank(method="first"), 10, labels=False)
    cal = pool.groupby("bin").agg(mean_pred=("p_rf", "mean"), mean_actual=("y", "mean"), n=("y", "size")).reset_index()
    print("  calibration (deciles of predicted score; out-of-fold, unseen sites):")
    print(cal.round(4).to_string(index=False))

    summ = build_summary()
    paths = {
        "json": os.path.join(OUT_DIR, "validation_results.json"),
        "summary": os.path.join(OUT_DIR, "validation_summary.csv"),
        "site": os.path.join(OUT_DIR, "validation_per_site.csv"),
        "cat": os.path.join(OUT_DIR, "validation_per_category.csv"),
        "png": os.path.join(OUT_DIR, "validation_r2_comparison.png"),
    }
    for p_ in paths.values():
        backup_if_exists(p_)
    summ.to_csv(paths["summary"], index=False)
    per_site.to_csv(paths["site"], index=False)
    per_cat.to_csv(paths["cat"], index=False)
    plot_r2(summ, paths["png"])
    RESULTS["summary"] = summ.to_dict("records")
    RESULTS["calibration"] = cal.to_dict("records")
    RESULTS["per_category"] = per_cat.to_dict("records")
    RESULTS["all_fold_rows"] = ROWS
    RESULTS["finished"] = datetime.now().isoformat()
    with open(paths["json"], "w") as f:
        json.dump(RESULTS, f, indent=2, default=jdefault)
    print("  wrote: " + ", ".join(os.path.basename(v) for v in paths.values()))

    # ------------------------------------------------------------------ final
    hdr("FINAL SUMMARY (core splits; every row is labelled with its split)")
    core = summ[summ["split"].isin(CORE)][["split", "model", "n_folds", "mae_mean", "mae_sd", "r2_mean", "r2_sd"]]
    print(core.round(4).to_string(index=False))
    snap_after = snapshot()
    changed = [k for k in snap_before if snap_before[k] != snap_after.get(k)]
    print("")
    print("READ-ONLY CHECK on the models and data folders: " + ("OK, nothing changed" if not changed else "CHANGED: %s" % changed))
    print("Total time: %.1f minutes" % ((time.time() - T0) / 60.0))


if __name__ == "__main__":
    main()
