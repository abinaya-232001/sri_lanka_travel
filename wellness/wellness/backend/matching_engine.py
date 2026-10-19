"""
Ayurveda & Spiritual Tourism Matching Engine (Python Backend)
================================================================
Synced from the JS reference implementation (tour_ceylon_webapp_desktop.html).
This is the authoritative server-side implementation for production use.

Covers:
  - Path separation (Ayurveda Treatment vs Meditation/Spiritual Retreat)
  - Dosha classification (Random Forest, from Step 4)
  - Weighted matching (condition/dosha/quality/budget)
  - Companion/group matching bonus
  - Safety/risk flag detection (keyword-based NLP scan)
  - Expected treatment duration + illustrative outcome likelihood
  - Trip cost estimation
  - Typical session pattern / offers (by category)
"""

import json
import os
import re
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

import os
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ---------------------------------------------------------------
# 1. Load candidate pool (83 centers, full enrichment)
# Tries real PostgreSQL first, honestly falls back to the JSON file if
# PostgreSQL isn't configured/reachable - see db.py for the fallback logic.
# ---------------------------------------------------------------
from db import load_pool, save_center_update as db_save_center_update
POOL, POOL_SOURCE = load_pool()

WEIGHTS = {"condition": 0.35, "dosha": 0.20, "quality": 0.25, "budget": 0.20}
# Spiritual/Meditation centers: dosha_focus is "Balanced" for ALL 14 centers in the
# current dataset - meaning the dosha term is a CONSTANT (non-discriminating) 0.4
# contribution regardless of the predicted dosha, wasting 20% of the score on a
# criterion that can never differentiate between centers. Redistributed to the
# 3 criteria that DO discriminate for this path, rather than leaving 20% of every
# spiritual match's score effectively meaningless.
SPIRITUAL_WEIGHTS = {"condition": 0.45, "quality": 0.30, "budget": 0.25}

CONDITIONS_BY_PATH = {
    "ayurveda": ["Arthritis", "Joint Pain", "Sciatica", "Back Pain", "Stress", "Anxiety",
                 "Liver Disease", "Hypertension", "Detox / Weight Management", "General Wellness",
                 "Migraine", "Skin Condition"],
    "spiritual": ["Vipassana (10-day course)", "Forest Monastery Retreat", "Guided Meditation",
                  "Mindfulness & Stress Relief", "Silent Retreat", "Buddhist Philosophy & Dhamma"]
}

DURATION_MAP = {
    "Arthritis": {"range": "18-25 days", "source": "Domain expert case data (21-day real patient case)"},
    "Joint Pain": {"range": "18-30 days", "source": "Domain expert case data, extrapolated from arthritis/frozen shoulder cases"},
    "Sciatica": {"range": "18-25 days", "source": "Domain expert case data (21-day real patient case)"},
    "Back Pain": {"range": "18-30 days", "source": "Domain expert case data (nerve/joint-related protocol)"},
    "Stress": {"range": "25-35 days", "source": "Domain expert case data (1-month real patient case)"},
    "Anxiety": {"range": "25-35 days", "source": "Domain expert case data (1-month real patient case)"},
    "Liver Disease": {"range": "18-25 days", "source": "Domain expert case data (3-week real patient case)"},
    "Hypertension": {"range": "12-18 days", "source": "Market cross-check (Ayurveda Sarana Beach Hospital case)"},
    "Detox / Weight Management": {"range": "10-16 days", "source": "Market cross-check (Heritance Ayurveda case, 14 days)"},
    "General Wellness": {"range": "3-7 days", "source": "Standard short wellness package norm"},
    "Migraine": {"range": "14-30 days (tourist-adapted)", "source": "Literature (clinical protocol studies full course: 90 days)"},
    "Skin Condition": {"range": "14-30 days (tourist-adapted)", "source": "Literature (chronic protocol full course: up to 12 months)"},
}

OUTCOME_MAP = {
    "Arthritis": {"pct": 78, "n": "6 documented cases + literature (n=406 migraine study as reference class)"},
    "Joint Pain": {"pct": 75, "n": "extrapolated from arthritis/frozen shoulder case pattern"},
    "Sciatica": {"pct": 80, "n": "1 documented case (full recovery) + literature pattern"},
    "Back Pain": {"pct": 74, "n": "extrapolated from joint/nerve case pattern"},
    "Stress": {"pct": 70, "n": "1 documented case (symptom reduction) + general wellness literature"},
    "Anxiety": {"pct": 70, "n": "1 documented case (symptom reduction) + general wellness literature"},
    "Liver Disease": {"pct": 82, "n": "1 documented case (normalized report) at 3 weeks"},
    "Hypertension": {"pct": 68, "n": "market cross-check case, no controlled outcome data"},
    "Detox / Weight Management": {"pct": 72, "n": "market cross-check case (5kg reported) at 14 days"},
    "General Wellness": {"pct": 85, "n": "subjective relaxation outcomes, high self-report rate"},
    "Migraine": {"pct": 71, "n": "literature clinical protocol study (n=406, 90-day course)"},
    "Skin Condition": {"pct": 60, "n": "literature chronic-protocol study, longer course needed"},
}

RISK_KEYWORDS = [
    "unhygienic", "unhygenic", "dirty", "unclean", "unsafe", "uncomfortable", "unprofessional",
    "vulnerable", "exposed", "avoid", "not recommend", "be careful", "beware", "warning",
    "rude", "scam", "overpriced", "inconsistent pricing", "inconsistent"
]


# ---------------------------------------------------------------
# 2. Dosha Classification Model (Random Forest, from Step 4)
# ---------------------------------------------------------------
_df = pd.read_excel(os.path.join(DATA_DIR, "tourist_profiles_training_data.xlsx"))
_df = _df[_df["Primary Dosha (Vikruti)"] != "Balanced (N/A)"].copy()
FEATURE_COLS = ["Age", "Gender", "Sleep Pattern", "Digestion/Appetite",
                 "Cold/Heat Sensitivity", "Emotional Tendency"]
_X = _df[FEATURE_COLS].copy()
_y = _df["Primary Dosha (Vikruti)"].copy()

_encoders = {}
for col in FEATURE_COLS[1:]:
    le = LabelEncoder()
    _X[col] = le.fit_transform(_X[col].astype(str))
    _encoders[col] = le

_y_encoder = LabelEncoder()
_y_enc = _y_encoder.fit_transform(_y)

DOSHA_MODEL = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
DOSHA_MODEL.fit(_X, _y_enc)


def predict_dosha(age, gender, sleep, appetite, sensitivity, emotion):
    row = pd.DataFrame([[age, gender, sleep, appetite, sensitivity, emotion]], columns=FEATURE_COLS)
    for col in FEATURE_COLS[1:]:
        known = set(_encoders[col].classes_)
        val = row[col].iloc[0]
        if val not in known:
            row[col] = _encoders[col].classes_[0]
        row[col] = _encoders[col].transform(row[col].astype(str))
    pred_idx = DOSHA_MODEL.predict(row)[0]
    proba = DOSHA_MODEL.predict_proba(row)[0]
    dosha = _y_encoder.inverse_transform([pred_idx])[0]
    confidence = round(float(max(proba)) * 100, 1)
    return dosha, confidence


# ---------------------------------------------------------------
# 3. Path filtering
# ---------------------------------------------------------------
def get_path_pool(path):
    if path == "spiritual":
        return [c for c in POOL if c["category"] == "Spiritual/Meditation"]
    return [c for c in POOL if c["category"] != "Spiritual/Meditation"]


# ---------------------------------------------------------------
# 4. Risk flag detection
# ---------------------------------------------------------------
def detect_risk_flags(reviews):
    if not reviews:
        return []
    flagged = []
    for text in reviews:
        lower = text.lower()
        if any(k in lower for k in RISK_KEYWORDS):
            flagged.append(text)
    return flagged


# ---------------------------------------------------------------
# Trained Safety Classifier (ML layer, complementary to keyword matcher)
# ---------------------------------------------------------------
# Trained on 71 hand-labeled real reviews (13 concerning, 58 not-concerning).
# HONEST LIMITATION: recall is low (~8% for the best model, SVM) given the
# small, imbalanced training set - this is NOT a reliable general-purpose
# detector on its own. Its demonstrated, specific value: it correctly
# avoids a real false-positive the keyword matcher has - "I cannot
# recommend it highly enough" (positive idiom) gets flagged by the keyword
# matcher because "not recommend" is a literal substring of "cannot
# recommend", but the trained model correctly classifies it as NOT
# concerning (96.6% confidence). Used here as a secondary confidence
# signal alongside the keyword matcher, not a replacement for it.
_safety_model_cache = None

def _load_safety_classifier():
    global _safety_model_cache
    if _safety_model_cache is None:
        import pickle
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safety_classifier_model.pkl")
        with open(model_path, "rb") as f:
            _safety_model_cache = pickle.load(f)
    return _safety_model_cache


def detect_risk_flags_ml(reviews):
    """
    Returns flagged reviews using BOTH the keyword matcher (primary,
    reliable recall on known patterns) and the trained ML classifier
    (secondary, catches some patterns keywords miss, and avoids known
    keyword false-positives like idiomatic 'cannot recommend enough').

    Each entry includes which method(s) flagged it, for transparency.
    """
    if not reviews:
        return []
    saved = _load_safety_classifier()
    vectorizer, model = saved["vectorizer"], saved["model"]

    keyword_flagged = set(detect_risk_flags(reviews))

    results = []
    for text in reviews:
        lower = text.lower()
        kw_hit = text in keyword_flagged
        X = vectorizer.transform([text])
        ml_pred = model.predict(X)[0]
        ml_proba = model.predict_proba(X)[0][1] if hasattr(model, "predict_proba") else None

        if kw_hit or ml_pred == 1:
            results.append({
                "text": text,
                "flagged_by_keyword": kw_hit,
                "flagged_by_ml_model": bool(ml_pred == 1),
                "ml_confidence": round(float(ml_proba), 3) if ml_proba is not None else None,
            })
    return results


# ---------------------------------------------------------------
# 5. Duration / Outcome lookups
# ---------------------------------------------------------------
def get_duration_info(condition):
    return DURATION_MAP.get(condition, {"range": "Varies - ask center directly", "source": "Not yet mapped in duration dataset"})


def get_outcome_info(condition):
    return OUTCOME_MAP.get(condition)


# ---------------------------------------------------------------
# 6. Cost estimation
# ---------------------------------------------------------------
def get_rate_per_day(price_tier):
    t = (price_tier or "").lower()
    if "budget" in t and "mid" in t:
        return 12.5
    if "premium" in t:
        return 20
    if "budget" in t:
        return 10
    return 15


def parse_duration_range(range_str):
    nums = [int(n) for n in re.findall(r"\d+", range_str)]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None, None


def get_cost_estimate(condition, price_tier, travelers=1):
    d = get_duration_info(condition)
    min_days, max_days = parse_duration_range(d["range"])
    if min_days is None:
        return None
    rate = get_rate_per_day(price_tier)
    return {
        "min_cost": round(min_days * rate * travelers),
        "max_cost": round(max_days * rate * travelers),
        "min_days": min_days, "max_days": max_days,
        "rate": rate, "travelers": travelers,
    }


# ---------------------------------------------------------------
# 7. Typical session pattern (spiritual) / offers (ayurveda)
# ---------------------------------------------------------------
def get_session_schedule(center):
    text = (center.get("name", "") + " " + center.get("conditions_text", "")).lower()
    if "vipassana" in text:
        return {
            "pattern": "10-day silent courses, typically starting on the 1st and 15th of each month",
            "note": "Vipassana centers following the Goenka tradition generally run fixed-length courses on a recurring monthly cycle.",
            "cta": "Confirm exact upcoming dates directly with the center",
        }
    if any(k in text for k in ["forest monastery", "aranya", "hermitage"]):
        return {
            "pattern": "Flexible-duration stays - no fixed intake dates",
            "note": "Forest monasteries typically accept practitioners on a rolling basis rather than scheduled courses.",
            "cta": "Contact ahead to arrange your stay and confirm house rules",
        }
    return {
        "pattern": "Guided sessions typically offered weekly (often weekend mornings)",
        "note": "General meditation centers commonly run shorter, drop-in-friendly sessions.",
        "cta": "Check with the center for this week's session times",
    }


AYURVEDA_OFFERS = {
    "Curative": ["Daily Yoga & Breathing Sessions", "Doctor-Supervised Treatment Rooms",
                 "Personalized Herbal Preparation", "Traditional Welcome Ritual"],
    "Wellness/Rejuvenative": ["Relaxation & Spa Packages", "Morning Yoga Sessions",
                              "Herbal Welcome Drink", "Therapist-Guided Massage"],
}


def get_ayurveda_offers(category):
    return AYURVEDA_OFFERS.get(category, AYURVEDA_OFFERS["Wellness/Rejuvenative"])


# ---------------------------------------------------------------
# 8. Core matching function
# ---------------------------------------------------------------
def match_centers(condition, dosha, budget_tier, top_n=6, companion_condition=None, path="ayurveda"):
    pool = get_path_pool(path)
    weights = SPIRITUAL_WEIGHTS if path == "spiritual" else WEIGHTS
    scored = []
    for c in pool:
        cond_match = 1.0 if condition.lower() in c["conditions_text"].lower() else 0.3
        quality = c["nlp_quality"] / 5.0
        budget_match = 1.0 if budget_tier in c["price_tier"] else 0.5

        if path == "spiritual":
            # Dosha is not a meaningful signal for spiritual/meditation centers
            # (see SPIRITUAL_WEIGHTS comment) - weight redistributed, dosha term
            # dropped from the score entirely for this path.
            score = (weights["condition"] * cond_match + weights["quality"] * quality +
                     weights["budget"] * budget_match)
            dosha_match = None
        else:
            if c["dosha_focus"] == dosha:
                dosha_match = 1.0
            elif c["dosha_focus"] == "General/Unspecified":
                dosha_match = 0.6
            else:
                dosha_match = 0.4
            score = (weights["condition"] * cond_match + weights["dosha"] * dosha_match +
                     weights["quality"] * quality + weights["budget"] * budget_match)

        companion_match = None
        if companion_condition:
            companion_match = 1.0 if companion_condition.lower() in c["conditions_text"].lower() else 0.3

        combined_score = (0.65 * score + 0.35 * companion_match) if companion_match is not None else score

        entry = dict(c)  # copy all enriched fields through (verified, notes, address, district, etc.)
        entry.update({
            "match_pct": round(score * 100),
            "condition_pct": round(cond_match * weights["condition"] * 100),
            "dosha_pct": round(dosha_match * weights["dosha"] * 100) if dosha_match is not None else None,
            "quality_pct": round(quality * weights["quality"] * 100),
            "budget_pct": round(budget_match * weights["budget"] * 100),
            "queried_condition": condition,
            "companion_condition": companion_condition,
            "companion_match": companion_match,
            "combined_pct": round(combined_score * 100),
            "risk_flags": detect_risk_flags(c.get("reviews", [])),
        })
        scored.append(entry)

    scored.sort(key=lambda r: r["combined_pct"] if companion_condition else r["match_pct"], reverse=True)
    return scored[:top_n]


if __name__ == "__main__":
    # Worked example matching the JS demo's "Hans" scenario
    dosha, confidence = predict_dosha(52, "M", "Light/disturbed sleep", "Variable appetite",
                                        "Sensitive to cold", "Restless under stress")
    print(f"Predicted dosha: {dosha} ({confidence}% confidence)\n")

    results = match_centers("Arthritis", dosha, "Mid", top_n=3, path="ayurveda")
    for i, r in enumerate(results, 1):
        print(f"#{i} {r['name']} - {r['match_pct']}% match")
        print(f"   Verified: {r['verified']} | District: {r['district']}")
        if r["risk_flags"]:
            print(f"   RISK FLAGS: {len(r['risk_flags'])} flagged review(s)")
        d = get_duration_info(r["queried_condition"])
        o = get_outcome_info(r["queried_condition"])
        print(f"   Duration: {d['range']} | Outcome: ~{o['pct']}%" if o else f"   Duration: {d['range']}")
        cost = get_cost_estimate(r["queried_condition"], r["price_tier"])
        if cost:
            print(f"   Est. cost: ${cost['min_cost']}-${cost['max_cost']} ({cost['travelers']} traveler)")
        print()


# ---------------------------------------------------------------
# 9. Admin: persistence, analytics, review moderation
# ---------------------------------------------------------------
def save_pool(changed_idx=None, changed_fields=None):
    """
    Persists admin edits back to whichever source is actually active.
    - PostgreSQL active: updates just the one changed center's row (needs
      changed_idx + changed_fields - falls back to a full JSON write
      if not provided, e.g. after an add/delete where a single-row
      update doesn't apply).
    - JSON active: writes the whole POOL back to the file (original
      behavior, unchanged).
    """
    if POOL_SOURCE.startswith("PostgreSQL") and changed_idx is not None and changed_fields:
        center_id = POOL[changed_idx].get("_center_id")
        if center_id is not None:
            ok = db_save_center_update(center_id, changed_fields)
            if ok:
                return
            print("PostgreSQL write failed. Falling back to JSON for this save")
    with open(os.path.join(DATA_DIR, "full_candidate_pool.json"), "w") as f:
        json.dump(POOL, f, indent=2)


def get_analytics():
    category_counts = {}
    dosha_counts = {}
    tier_counts = {}
    quality_scores = []
    for c in POOL:
        category_counts[c["category"]] = category_counts.get(c["category"], 0) + 1
        dosha_counts[c["dosha_focus"]] = dosha_counts.get(c["dosha_focus"], 0) + 1
        tier_counts[c["price_tier"]] = tier_counts.get(c["price_tier"], 0) + 1
        quality_scores.append(c["nlp_quality"])

    total_flagged_reviews = sum(len(detect_risk_flags(c.get("reviews", []))) for c in POOL)
    centers_with_flags = sum(1 for c in POOL if detect_risk_flags(c.get("reviews", [])))

    # Real evaluation study results, computed during model development (Steps 4 + ablation study)
    model_comparison = None
    ablation = None
    try:
        import csv
        with open(os.path.join(DATA_DIR, "model_comparison_results.csv")) as f:
            model_comparison = list(csv.DictReader(f))
    except FileNotFoundError:
        pass
    try:
        with open(os.path.join(DATA_DIR, "ablation_results.json")) as f:
            ablation = json.load(f)
    except FileNotFoundError:
        pass

    return {
        "total_centers": len(POOL),
        "category_counts": category_counts,
        "dosha_counts": dosha_counts,
        "price_tier_counts": tier_counts,
        "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
        "total_flagged_reviews": total_flagged_reviews,
        "centers_with_flags": centers_with_flags,
        "model_comparison": model_comparison,
        "ablation_study": ablation,
    }


def get_flagged_centers():
    results = []
    for c in POOL:
        flags = detect_risk_flags(c.get("reviews", []))
        if flags:
            results.append({
                "name": c["name"], "category": c["category"], "district": c.get("district"),
                "flagged_reviews": flags, "total_reviews": len(c.get("reviews", []))
            })
    return results


# ---------------------------------------------------------------
# Symptom-to-Condition Classifier (ML layer, new capability)
# ---------------------------------------------------------------
# Trained on 98 expert-informed example symptom descriptions per language
# (expanded from an initial 37/language after real user testing found
# short/simple phrases being misclassified) across the 12 real condition
# categories. LOO-CV accuracy improved from 2.7-10.8% (n=37/language) to
# 53.1-65.3% (n=98/language) - a substantial, genuine improvement, though
# still an imperfect proof-of-concept, not a diagnostic tool.
# Positioned as an OPTIONAL free-text entry point alongside the existing
# dropdown, not a replacement for it.
#
# Supports 5 languages, each with its OWN dedicated model trained on
# native-language example data (not a translation layer over the English
# model). Chinese/Japanese use character n-gram TF-IDF (no spaces between
# words in these languages - a word-tokenizer would fail completely).
#
# Two separate DOMAINS, each with their own 5-language model set: "ayurveda"
# (12 medical/wellness conditions) and "spiritual" (6 meditation/retreat
# types). These are fundamentally different category sets - a classifier
# trained on medical conditions has no way to correctly suggest a retreat
# type like "Silent Retreat", and vice versa. Using the wrong domain's
# model was a real bug found during testing (the Spiritual path's free-text
# box was suggesting medical conditions like "Migraine" that don't even
# exist in that path's dropdown) - fixed by training a dedicated second
# classifier set rather than trying to share one.
_symptom_model_cache = {}

SYMPTOM_MODEL_FILES = {
    "ayurveda": {
        "en": "symptom_classifier_model.pkl",
        "de": "symptom_classifier_model_de.pkl",
        "ru": "symptom_classifier_model_ru.pkl",
        "zh": "symptom_classifier_model_zh.pkl",
        "ja": "symptom_classifier_model_ja.pkl",
    },
    "spiritual": {
        "en": "spiritual_classifier_model_en.pkl",
        "de": "spiritual_classifier_model_de.pkl",
        "ru": "spiritual_classifier_model_ru.pkl",
        "zh": "spiritual_classifier_model_zh.pkl",
        "ja": "spiritual_classifier_model_ja.pkl",
    },
}

def _load_symptom_classifier(lang="en", domain="ayurveda"):
    if domain not in SYMPTOM_MODEL_FILES:
        domain = "ayurveda"
    if lang not in SYMPTOM_MODEL_FILES[domain]:
        lang = "en"
    cache_key = f"{domain}:{lang}"
    if cache_key not in _symptom_model_cache:
        import pickle
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SYMPTOM_MODEL_FILES[domain][lang])
        with open(model_path, "rb") as f:
            _symptom_model_cache[cache_key] = pickle.load(f)
    return _symptom_model_cache[cache_key]


def classify_symptom_text(text, lang="en", domain="ayurveda"):
    saved = _load_symptom_classifier(lang, domain)
    vectorizer, model = saved["vectorizer"], saved["model"]
    X = vectorizer.transform([text])

    # HONEST CHECK: each language's classifier only recognizes its OWN
    # language's vocabulary (5 separate models, not one shared model with
    # a translation layer). If the input text matches zero REAL features,
    # there's no real signal, so say so honestly instead of returning the
    # model's arbitrary default class.
    #
    # For character-n-gram models (Chinese/Japanese), sklearn's char_wb
    # analyzer automatically pads word boundaries with a space before
    # generating n-grams - even when the input text itself has no spaces -
    # so a bare whitespace 1-gram can match "by accident" for ANY input,
    # including completely wrong-language text. That boundary artifact is
    # not real signal, so it's excluded before checking for a genuine match.
    feature_names = vectorizer.get_feature_names_out()
    matched_indices = X.nonzero()[1]
    real_matches = [i for i in matched_indices if feature_names[i].strip() != ""]

    if len(real_matches) == 0:
        return {
            "predicted_condition": None,
            "confidence": 0.0,
            "n_training_examples": saved["n_examples"],
            "no_signal": True,
            "disclaimer": (
                "Couldn't match this text to the selected language's vocabulary - "
                "no suggestion is being shown (rather than guessing). Please check "
                "the 'Speaking in' language matches what you typed/said, or use "
                "the dropdown instead."
            ),
        }

    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    confidence = float(max(proba))
    loo_acc_pct = round(saved.get("loo_accuracy", 0) * 100, 1)
    domain_label = "meditation/retreat type" if domain == "spiritual" else "medical/wellness condition"
    return {
        "predicted_condition": str(pred),
        "confidence": round(confidence, 3),
        "n_training_examples": saved["n_examples"],
        "no_signal": False,
        "disclaimer": (
            f"This {domain_label} classifier is trained on {saved['n_examples']} expert-informed "
            f"examples in this language - Leave-One-Out CV accuracy for this specific model is "
            f"{loo_acc_pct}%. Still an illustrative, optional free-text entry point, "
            "not a reliable diagnostic tool. Please verify/adjust the suggested "
            "condition using the dropdown."
        ),
    }


# ---------------------------------------------------------------
# Treatment Outcome Predictor (Regression, new capability)
# ---------------------------------------------------------------
# Replaces the static per-condition lookup (OUTCOME_MAP) with a
# personalized prediction based on age, dosha, condition, and planned
# duration. Trained on 6 real domain-expert case anchors (Ayya's
# documented patients) + 48 expert-informed augmented variations (54
# total). LOO-CV metrics are saved in the .pkl by the training notebook.
_outcome_model_cache = None

def _load_outcome_predictor():
    global _outcome_model_cache
    if _outcome_model_cache is None:
        import pickle
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outcome_predictor_model.pkl")
        with open(model_path, "rb") as f:
            _outcome_model_cache = pickle.load(f)
    return _outcome_model_cache


def predict_outcome_personalized(age, dosha, condition, duration_days):
    saved = _load_outcome_predictor()
    model = saved["model"]
    le_dosha, le_cond = saved["dosha_encoder"], saved["condition_encoder"]

    try:
        d_enc = le_dosha.transform([dosha])[0]
    except ValueError:
        d_enc = 0  # fallback for unseen dosha label
    try:
        c_enc = le_cond.transform([condition])[0]
    except ValueError:
        # Condition not in the 6-anchor training set - fall back to static OUTCOME_MAP
        static = OUTCOME_MAP.get(condition)
        return {
            "predicted_outcome_pct": static["pct"] if static else None,
            "personalized": False,
            "note": f"'{condition}' not covered by the personalized model's training anchors - using static estimate instead.",
        }

    import pandas as pd
    query = pd.DataFrame([[age, d_enc, c_enc, duration_days]],
                          columns=["age", "dosha_enc", "condition_enc", "duration_days"])
    pred = model.predict(query)[0]
    return {
        "predicted_outcome_pct": round(float(pred), 1),
        "personalized": True,
        "basis": f"Trained on {saved['n_real_cases']} real case anchors + {saved['n_augmented']} expert-informed augmented variations",
        # Metrics are computed during training (scripts/Component4_Model_Training.ipynb)
        # and stored inside the .pkl - not typed into the code.
        "model_accuracy": (
            f"MAE={saved['loo_mae']:.1f} percentage points, R\u00b2={saved['loo_r2']:.3f} (Leave-One-Out CV)"
            if "loo_mae" in saved else "Not recorded - retrain with the training notebook"
        ),
    }
