"""
models.py - the trained Random-Forest models wrapped as a policy for planner.Planner.

  Model 1  Attraction RF  : (user message, attraction row)  -> relevance grade 0..3
           (uses two helper intent RFs: message -> category, message -> mood)
  Model 2  Accommodation RF: (comfort, budget, meal plan, attraction location, hotel) -> suitability 0..2
  Model 3  Visit-time RF   : (user mood, slot, current day state) -> "choose this slot next" (yes / no)
"""
import os
import joblib
import numpy as np
import pandas as pd
from common import (MODELS, attraction_feature_frame, hotel_feature_frame, slot_feature_rows)


def expected(proba, classes):
    return proba @ np.asarray(classes, dtype=float)


def intent_probs(bundle, msg):
    X = bundle["intent_vec"].transform([msg])
    pc = dict(zip(bundle["rf_cat"].classes_, bundle["rf_cat"].predict_proba(X)[0]))
    pm = dict(zip(bundle["rf_mood"].classes_, bundle["rf_mood"].predict_proba(X)[0]))
    return pc, pm


def best_mood_slots(a, mood_score):
    df = pd.DataFrame({"AttrID": a["AttrID"].values, "RowID": a["RowID"].values, "s": mood_score})
    return df.loc[df.groupby("AttrID")["s"].idxmax()].set_index("AttrID")["RowID"].to_dict()


class RFPolicy:
    def __init__(self, a, h, bundle=None):
        self.a, self.h = a, h
        self.b = bundle or joblib.load(os.path.join(MODELS, "travel_rf_models.joblib"))
        self.te = self.b["text_engine"]

    # ---------------- Model 1 ----------------
    def attraction_context(self, msg, month):
        pc, pm = intent_probs(self.b, msg)
        F = attraction_feature_frame(self.a, self.te, msg, month, pc, pm)
        rf = self.b["rf_attr"]
        row_score = expected(rf.predict_proba(F), rf.classes_)
        attr_score = pd.Series(row_score).groupby(self.a["AttrID"].values).max().to_dict()
        mood_score = np.array([pm.get(m, 0) for m in self.a["Mood"]]) + F["sim_mood_word"].values
        return {"attr_score": attr_score, "row_score": row_score, "mood_intent": pm,
                "mood_word_sim": F["sim_mood_word"].values, "mood_prof_sim": F["sim_mood_profile"].values,
                "best_mood_slot": best_mood_slots(self.a, mood_score),
                "top_moods": [k for k, _ in sorted(pm.items(), key=lambda x: -x[1])[:3]],
                "top_categories": [k for k, _ in sorted(pc.items(), key=lambda x: -x[1])[:3]]}

    # ---------------- Model 3 ----------------
    def choose_slot(self, cands, chosen, cursor, ctx, force=False):
        X = slot_feature_rows(cands, chosen, cursor, ctx["attr_score"], ctx["mood_intent"],
                              ctx["mood_word_sim"], ctx["mood_prof_sim"], ctx["best_mood_slot"])
        p = self.b["rf_slot"].predict_proba(X)[:, list(self.b["rf_slot"].classes_).index(1)]
        k = int(np.argmax(p))
        return k if (p[k] >= self.b.get("slot_threshold", 0.5) or force) else None

    # ---------------- Model 2 ----------------
    def hotel_scores(self, lat, lon, comfort, plan, budget_pn):
        F = hotel_feature_frame(self.h, lat, lon, comfort, plan, budget_pn, self.b["hotel_categories"])
        rf = self.b["rf_hotel"]
        return expected(rf.predict_proba(F[self.b["hotel_features"]]), rf.classes_)
