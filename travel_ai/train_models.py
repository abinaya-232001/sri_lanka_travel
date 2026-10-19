"""
train_models.py - trains the Random-Forest models from the workbooks in training_data/
and saves them to models/travel_rf_models.joblib (+ metrics.json).

    python build_training_data.py   # (re)create training workbooks
    python train_models.py          # train + evaluate
"""
import json, os, time
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold, cross_val_predict, StratifiedKFold
from sklearn.pipeline import FeatureUnion
from common import (Gazetteer, load_attractions, load_hotels, TextEngine, attraction_feature_frame, ATTR_FEATURES,
                    hotel_feature_frame, slot_candidates, slot_feature_rows, SLOT_FEATURES, to_minutes,
                    TRAIN, MODELS)
from models import expected, best_mood_slots, intent_probs

RS = 42


def rf(n=250, leaf=3, depth=None, cw=None):
    return RandomForestClassifier(n_estimators=n, min_samples_leaf=leaf, max_depth=depth, n_jobs=-1,
                                  random_state=RS, class_weight=cw)


def ndcg_at_k(grades_sorted, ideal_sorted, k=10):
    disc = 1 / np.log2(np.arange(2, k + 2))
    dcg = ((2 ** np.asarray(grades_sorted[:k]) - 1) * disc[:len(grades_sorted[:k])]).sum()
    idcg = ((2 ** np.asarray(ideal_sorted[:k]) - 1) * disc[:len(ideal_sorted[:k])]).sum()
    return dcg / idcg if idcg > 0 else np.nan


def train_hotel_model(h, metrics, t0):
    """Model 2: hotel suitability from accommodation_training.xlsx."""
    ht = pd.read_excel(os.path.join(TRAIN, "accommodation_training.xlsx"), sheet_name="Accommodation Training")
    hy = [c for c in ht.columns if c.startswith("Suitability")][0]
    cats = sorted(h["Category"].unique())
    hfe, hys, hg, hfit = [], [], [], []
    hid_to_pos = {hid: p for p, hid in enumerate(h["HotelID"])}
    for sid, grp in ht.groupby("Scenario ID", sort=False):
        r0 = grp.iloc[0]
        F = hotel_feature_frame(h, r0["Attraction Lat"], r0["Attraction Lon"], r0["User Comfort Level"], r0["Meal Plan"],
                                r0["Budget per Night (LKR)"], cats)
        pos = [hid_to_pos[x] for x in grp["HotelID"]]
        hfe.append(F.iloc[pos]); hys.append(grp[hy].values); hg += [sid] * len(grp)
        near = F["distance_km"].values <= max(20.0, np.sort(F["distance_km"].values)[9])
        any_fit = bool((near & (F["price_per_night"].values <= r0["Budget per Night (LKR)"])).any())
        hfit += [any_fit] * len(grp)
    XH = pd.concat(hfe, ignore_index=True); yH = np.concatenate(hys); gH = np.array(hg); fitH = np.array(hfit)
    hotel_features = list(XH.columns)
    oofH = np.zeros(len(yH))
    for tr, te_i in GroupKFold(5).split(XH, yH, gH):
        m = rf(150, 3).fit(XH.iloc[tr], yH[tr])
        oofH[te_i] = expected(m.predict_proba(XH.iloc[te_i]), m.classes_)
    res = {True: [], False: []}
    for sid in np.unique(gH):
        mk = gH == sid
        if yH[mk].max() == 0:
            continue
        g = yH[mk][np.argmax(oofH[mk])]
        res[bool(fitH[mk][0])].append((g >= 1, g == 2))
    metrics["hotel_top1_suitable_cv"] = float(np.mean([a for a, _ in res[True]]))
    metrics["hotel_top1_best_cv"] = float(np.mean([b for _, b in res[True]]))
    metrics["hotel_budget_too_low_top1_in_cheapest_tier_cv"] = float(np.mean([a for a, _ in res[False]])) if res[False] else None
    metrics["hotel_scenarios_budget_too_low"] = len(res[False])
    rf_hotel = rf(250, 3).fit(XH, yH)
    metrics["hotel_feature_importance"] = dict(sorted(zip(hotel_features, map(float, rf_hotel.feature_importances_)), key=lambda x: -x[1])[:15])
    print("hotel RF:", {k: v for k, v in metrics.items() if k.startswith("hotel") and "importance" not in k}, f"{time.time()-t0:.0f}s")
    return rf_hotel, cats, hotel_features


def train_slot_model(a, te, bundle, metrics, t0):
    """Model 3: learns which slot to take next (and when to stop) from the sample itineraries."""
    rf_attr = bundle["rf_attr"]
    vt = pd.read_excel(os.path.join(TRAIN, "visit_time_training.xlsx"))
    SX, SY, SG, STEP = [], [], [], []
    ctx_cache = {}
    for (sid, day), grp in vt.groupby(["Sample ID", "Day"], sort=False):
        grp = grp.sort_values("Order")
        msg, month = grp["User Message"].iloc[0], int(grp["Travel Month"].iloc[0])
        if sid not in ctx_cache:
            pc, pm = intent_probs(bundle, msg)
            F = attraction_feature_frame(a, te, msg, month, pc, pm)
            rs = expected(rf_attr.predict_proba(F), rf_attr.classes_)
            ctx_cache[sid] = {
                "attr_score": pd.Series(rs).groupby(a["AttrID"].values).max().to_dict(), "mood_intent": pm,
                "mood_word_sim": F["sim_mood_word"].values, "mood_prof_sim": F["sim_mood_profile"].values,
                "best_mood_slot": best_mood_slots(a, np.array([pm.get(m, 0) for m in a["Mood"]]) + F["sim_mood_word"].values)}
        c = ctx_cache[sid]
        pool = grp["Day Pool (AttrIDs)"].iloc[0].split(" || ")
        rows = a[a["AttrID"].isin(pool)]
        chosen, cursor, last = [], None, None
        seq = list(grp["RowID"]) + [None]  # None = expert stopped
        for k, target in enumerate(seq):
            cands = slot_candidates(rows, chosen, cursor, last)
            if not cands:
                break
            X = slot_feature_rows(cands, chosen, cursor, c["attr_score"], c["mood_intent"], c["mood_word_sim"],
                                  c["mood_prof_sim"], c["best_mood_slot"])
            y = np.array([int(r["RowID"] == target) for r, _ in cands])
            SX.append(X); SY.append(y); SG += [sid] * len(y); STEP += [f"{sid}-{day}-{k}"] * len(y)
            if target is None:
                break
            r = a.iloc[target]
            chosen.append(r); cursor, last = r["EndMin"], (r["Lat"], r["Lon"])
    XS = pd.concat(SX, ignore_index=True); yS = np.concatenate(SY); gS = np.array(SG); stS = np.array(STEP)
    print("slot rows:", XS.shape, yS.mean(), f"{time.time()-t0:.0f}s")
    oofS = np.zeros(len(yS))
    for tr, te_i in GroupKFold(5).split(XS, yS, gS):
        m = rf(200, 2).fit(XS.iloc[tr], yS[tr])
        oofS[te_i] = m.predict_proba(XS.iloc[te_i])[:, 1]
    df = pd.DataFrame({"step": stS, "y": yS, "p": oofS})
    steps = []
    for step, g in df.groupby("step"):
        k = g["p"].values.argmax()
        steps.append((step.endswith("-0"), g["y"].sum() > 0, bool(g["y"].values[k] == 1), g["p"].max()))

    def acc(th):
        ok = []
        for first, has_pos, top_ok, pmax in steps:
            go = first or pmax >= th
            ok.append((go and top_ok) if has_pos else (not go))
        return float(np.mean(ok))
    grid = np.round(np.arange(0.05, 0.71, 0.01), 2)
    scores = [acc(th) for th in grid]
    th = float(grid[int(np.argmax(scores))])
    metrics["visit_time_threshold (tuned on CV)"] = th
    metrics["visit_time_step_accuracy_cv @0.5"] = acc(0.5)
    metrics["visit_time_step_accuracy_cv @tuned"] = max(scores)
    metrics["visit_time_slot_choice_accuracy_cv"] = float(np.mean([s[2] for s in steps if s[1]]))
    metrics["visit_time_stop_accuracy_cv"] = float(np.mean([(s[3] < th) for s in steps if not s[1] and not s[0]] or [np.nan]))
    rf_slot = rf(250, 2).fit(XS, yS)
    metrics["visit_time_feature_importance"] = dict(sorted(zip(SLOT_FEATURES, map(float, rf_slot.feature_importances_)), key=lambda x: -x[1]))
    bundle["rf_slot"], bundle["slot_threshold"] = rf_slot, th
    print("slot RF:", {k: v for k, v in metrics.items() if k.startswith("visit_time") and "importance" not in k}, f"{time.time()-t0:.0f}s")


def main():
    t0 = time.time()
    os.makedirs(MODELS, exist_ok=True)
    gz = Gazetteer(); a = load_attractions(gz); h = load_hotels(gz)
    te = TextEngine().fit(a)
    metrics = {}

    # =========================== intent RFs (message -> category / mood) =========
    intents = pd.read_excel(os.path.join(TRAIN, "attraction_training.xlsx"), sheet_name="Message Intents")
    intents["Intended Mood"] = intents["Intended Mood"].fillna("")
    vec = FeatureUnion([("w", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_features=8000)),
                        ("c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=3, max_features=12000))])
    Xm = vec.fit_transform(intents["User Message"].tolist() + te.full)[: len(intents)]
    rf_cat = rf(200, 1)
    cv = StratifiedKFold(5, shuffle=True, random_state=RS)
    oof_cat = cross_val_predict(rf_cat, Xm, intents["Intended Category"], cv=cv, method="predict_proba")
    rf_cat.fit(Xm, intents["Intended Category"])
    has_mood = intents["Intended Mood"] != ""
    rf_mood = rf(200, 1)
    oof_mood_part = cross_val_predict(rf_mood, Xm[has_mood.values], intents.loc[has_mood, "Intended Mood"], cv=cv, method="predict_proba")
    rf_mood.fit(Xm[has_mood.values], intents.loc[has_mood, "Intended Mood"])
    # messages without a mood word: out-of-sample by construction (not in mood training)
    oof_mood = np.zeros((len(intents), len(rf_mood.classes_)))
    oof_mood[has_mood.values] = oof_mood_part
    oof_mood[~has_mood.values] = rf_mood.predict_proba(Xm[~has_mood.values])
    metrics["intent_category_accuracy_cv"] = float((rf_cat.classes_[oof_cat.argmax(1)] == intents["Intended Category"]).mean())
    metrics["intent_mood_accuracy_cv"] = float((rf_mood.classes_[oof_mood_part.argmax(1)] == intents.loc[has_mood, "Intended Mood"]).mean())
    print("intent RFs:", metrics["intent_category_accuracy_cv"], metrics["intent_mood_accuracy_cv"], f"{time.time()-t0:.0f}s")

    # =========================== Model 1: attraction relevance RF =================
    at = pd.read_excel(os.path.join(TRAIN, "attraction_training.xlsx"), sheet_name="Attraction Training")
    ycol = [c for c in at.columns if c.startswith("Relevance")][0]
    idx = {sid: i for i, sid in enumerate(intents["Sample ID"])}
    feats, ys, groups = [], [], []
    for sid, grp in at.groupby("Sample ID", sort=False):
        i = idx[sid]
        pc = dict(zip(rf_cat.classes_, oof_cat[i])); pm = dict(zip(rf_mood.classes_, oof_mood[i]))
        F = attraction_feature_frame(a, te, grp["User Message"].iloc[0], int(grp["Travel Month"].iloc[0]), pc, pm)
        feats.append(F.iloc[grp["RowID"].values]); ys.append(grp[ycol].values); groups += [sid] * len(grp)
    XA = pd.concat(feats, ignore_index=True); yA = np.concatenate(ys); gA = np.array(groups)
    print("attraction features:", XA.shape, f"{time.time()-t0:.0f}s")
    rf_attr = rf(250, 5)
    gkf = GroupKFold(5)
    oof = np.zeros(len(yA))
    for tr, te_i in gkf.split(XA, yA, gA):
        m = rf(150, 5).fit(XA.iloc[tr], yA[tr])
        oof[te_i] = expected(m.predict_proba(XA.iloc[te_i]), m.classes_)
    nd, p5 = [], []
    for sid in np.unique(gA):
        mk = gA == sid
        order = np.argsort(-oof[mk]); gs = yA[mk][order]
        nd.append(ndcg_at_k(gs, np.sort(yA[mk])[::-1], 10)); p5.append(np.mean(gs[:5] >= 2))
    metrics["attraction_ndcg@10_cv"] = float(np.nanmean(nd))
    metrics["attraction_precision@5_cv (grade>=2)"] = float(np.mean(p5))
    rf_attr.fit(XA, yA)
    metrics["attraction_feature_importance"] = dict(sorted(zip(ATTR_FEATURES, map(float, rf_attr.feature_importances_)), key=lambda x: -x[1]))
    print("attraction RF:", metrics["attraction_ndcg@10_cv"], metrics["attraction_precision@5_cv (grade>=2)"], f"{time.time()-t0:.0f}s")

    rf_hotel, cats, hotel_features = train_hotel_model(h, metrics, t0)

    bundle = {"text_engine": te, "intent_vec": vec, "rf_cat": rf_cat, "rf_mood": rf_mood, "rf_attr": rf_attr}
    train_slot_model(a, te, bundle, metrics, t0)
    bundle.update({"rf_hotel": rf_hotel, "hotel_categories": cats, "hotel_features": hotel_features})
    joblib.dump(bundle, os.path.join(MODELS, "travel_rf_models.joblib"), compress=3)
    metrics["training_rows"] = {"intent_messages": int(len(intents)), "attraction_pairs": int(len(yA)),
                                "hotel_pairs": int(len(yH))}
    json.dump(metrics, open(os.path.join(MODELS, "metrics.json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in metrics.items() if "importance" not in k}, indent=2))
    print(f"done in {time.time()-t0:.0f}s")


def slot_only():
    """python train_models.py --slot-only : retrain just the visit-time model."""
    t0 = time.time()
    gz = Gazetteer(); a = load_attractions(gz)
    path = os.path.join(MODELS, "travel_rf_models.joblib")
    bundle = joblib.load(path)
    mpath = os.path.join(MODELS, "metrics.json")
    metrics = json.load(open(mpath)) if os.path.exists(mpath) else {}
    train_slot_model(a, bundle["text_engine"], bundle, metrics, t0)
    joblib.dump(bundle, path, compress=3)
    json.dump(metrics, open(mpath, "w"), indent=2)


def hotels_only():
    """python train_models.py --hotels-only : retrain just the accommodation model."""
    t0 = time.time()
    gz = Gazetteer(); h = load_hotels(gz)
    path = os.path.join(MODELS, "travel_rf_models.joblib")
    bundle = joblib.load(path)
    mpath = os.path.join(MODELS, "metrics.json")
    metrics = json.load(open(mpath)) if os.path.exists(mpath) else {}
    rf_hotel, cats, feats = train_hotel_model(h, metrics, t0)
    bundle.update({"rf_hotel": rf_hotel, "hotel_categories": cats, "hotel_features": feats})
    joblib.dump(bundle, path, compress=3)
    json.dump(metrics, open(mpath, "w"), indent=2)


if __name__ == "__main__":
    import sys
    if "--slot-only" in sys.argv:
        slot_only()
    elif "--hotels-only" in sys.argv:
        hotels_only()
    else:
        main()
