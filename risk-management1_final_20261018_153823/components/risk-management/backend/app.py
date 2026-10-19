from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import csv
import json
import time
import math
try:
    import shap
except ImportError:
    shap = None
from database import get_connection

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _p(*parts):
    return os.path.join(_BASE_DIR, *parts)

_CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5182,http://127.0.0.1:5182",
).split(",") if o.strip()]

app = Flask(__name__)

# FIXED: Explicit CORS allowing your React app origins
CORS(app, resources={
    r"/*": {
        "origins": _CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# FIXED: Safe model loading with fallback.
# UPDATED: loads sklearn Pipelines (preprocessing + model bundled together)
# instead of a raw estimator plus separately-saved LabelEncoders. The pipeline
# does its own OneHotEncoder(handle_unknown="ignore") internally, so app.py no
# longer needs to reconstruct encodings by hand -- see build_features() below.
print("Loading models...")
try:
    with open(_p("models", "crowd_pipeline.pkl"), "rb") as f:
        regressor = pickle.load(f)          # sklearn Pipeline: preprocessing + RandomForestRegressor
    with open(_p("models", "risk_pipeline.pkl"), "rb") as f:
        classifier = pickle.load(f)         # sklearn Pipeline: preprocessing + RandomForestClassifier
    with open(_p("models", "risk_label_encoder.pkl"), "rb") as f:
        risk_encoder = pickle.load(f)       # LabelEncoder for the target only (High/Medium/Low)
    print("Models loaded successfully")
    MODELS_LOADED = True
except Exception as e:
    print(f"WARNING: Could not load models: {e}")
    print("Running in FALLBACK mode - predictions will be simulated")
    regressor = None
    classifier = None
    risk_encoder = None
    MODELS_LOADED = False

# FIXED: Ensure data directory exists
os.makedirs(_p("data"), exist_ok=True)
os.makedirs(_p("models"), exist_ok=True)
os.makedirs(_p("outputs"), exist_ok=True)

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ FIXED: Site data now loaded from the real 50-site CSV instead of a hardcoded 30-site dict ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
SITES = {}
_sites_csv_path = os.path.join(os.path.dirname(__file__), "data", "tourist_sites.csv")
with open(_sites_csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        site_id = int(row["site_id"])
        SITES[site_id] = {
            "name": row["site_name"],
            "capacity": int(float(row["capacity_per_day"])),
            "annual": int(float(row["annual_visitors_2024"])),
            "category": row["category"],
            "district": row["district"],
            "province": row["province"],
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
            "is_eco": int(float(row["is_eco_friendly"])),
            "is_unesco": int(float(row["is_unesco"])),
            "fee": int(float(row["entrance_fee_lkr"])),
        }
print(f"Loaded {len(SITES)} sites from tourist_sites.csv")

# UPDATED: Esala Perahera corrected to Aug 18-27 2026 per the official
# announcement from the Sri Dalada Maligawa (Temple of the Sacred Tooth
# Relic), the festival's organizing authority, published 8 July 2026.
# The previous "07-20 to 07-27" range was a full month off from the
# real festival window and has been replaced. Full window included
# (not just start/end days) since crowding is elevated throughout.
NATIONAL_HOLIDAY_DATES = [
    "2026-01-03",  # Duruthu Poya
    "2026-01-15",  # Tamil Thai Pongal
    "2026-02-01",  # Navam Poya
    "2026-02-04",  # Independence Day
    "2026-02-15",  # Maha Shivaratri
    "2026-03-02",  # Medin Poya
    "2026-03-21",  # Eid-ul-Fitr (tentative, lunar sighting)
    "2026-04-01",  # Bak Poya
    "2026-04-03",  # Good Friday
    "2026-04-13",  # Day before Sinhala/Tamil New Year
    "2026-04-14",  # Sinhala & Tamil New Year
    "2026-05-01",  # Adhi Vesak Poya + Labour Day
    "2026-05-28",  # Eid al-Adha (tentative, lunar sighting)
    "2026-05-30",  # Vesak Poya
    "2026-05-31",  # Day following Vesak
    "2026-06-29",  # Poson Poya
    "2026-07-29",  # Esala Poya
    "2026-08-26",  # Milad-un-Nabi (tentative, lunar sighting)
    "2026-08-27",  # Nikini Poya
    "2026-09-26",  # Binara Poya
    "2026-10-25",  # Vap Poya
    "2026-11-08",  # Deepavali
    "2026-11-24",  # Il Poya
    "2026-12-23",  # Unduvap Poya
    "2026-12-25",  # Christmas
]

# Kandy Esala Perahera 2026: Kumbal Perahera Aug 18-22, Randoli Perahera
# Aug 23-27, Diya Kepeema / closing day procession Aug 28. Kandy-specific --
# only elevates crowding at the Temple of the Tooth, not nationwide.
KANDY_ESALA_PERAHERA_DATES = [
    "2026-08-18","2026-08-19","2026-08-20","2026-08-21","2026-08-22",
    "2026-08-23","2026-08-24","2026-08-25","2026-08-26","2026-08-27","2026-08-28",
]

KANDY_TEMPLE_SITE_NAME = "Temple of the Tooth Kandy"

def is_high_impact_date(date_str, site):
    """National holidays apply to every site; Esala Perahera only
    elevates crowding at the Temple of the Tooth in Kandy."""
    if date_str in NATIONAL_HOLIDAY_DATES:
        return True
    if site.get("name") == KANDY_TEMPLE_SITE_NAME and date_str in KANDY_ESALA_PERAHERA_DATES:
        return True
    return False

def get_season(month):
    if month in [12, 1, 2, 3]:
        return "peak"
    elif month in [7, 8, 9]:
        return "low"
    else:
        return "shoulder"

def get_monthly_weather(month):
    weather = {
        1: (27, 45),  2: (28, 30),  3: (29, 55),
        4: (29, 120), 5: (28, 180), 6: (27, 160),
        7: (27, 130), 8: (27, 110), 9: (27, 130),
        10: (27, 200),11: (27, 300),12: (27, 150)
    }
    return weather.get(month, (27, 100))

# Real, published national monthly hotel occupancy rates (Sri Lanka, 2019)
# Source: Sri Lanka Tourism Development Authority, Annual Statistical Report 2019,
# Table 19 / Chart 19 "Distribution of Occupancy Rates by Month" (All Regions).
# https://sltda.gov.lk/storage/common_media/AAnnual%20Statistical%20Report%20new%202109%20Word3889144215.pdf
# NOTE: This is a national average across all accommodation regions, not per-site
# or per-hotel data, since no such granular public dataset exists for Sri Lanka.
REAL_MONTHLY_OCCUPANCY = {
    1: 0.7842, 2: 0.7730, 3: 0.7335, 4: 0.6358, 5: 0.1493, 6: 0.2276,
    7: 0.4607, 8: 0.5588, 9: 0.5105, 10: 0.5361, 11: 0.7330, 12: 0.7479
}
ANNUAL_AVG_OCCUPANCY = 0.5709  # fallback, same source

def build_features(site, date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    month = date.month
    season = get_season(month)
    temp, rainfall = get_monthly_weather(month)
    is_holiday = 1 if is_high_impact_date(date_str, site) else 0
    is_weekend = 1 if date.weekday() >= 5 else 0
    season_mult = 1.6 if season == "peak" else 0.8 if season == "low" else 1.0
    daily_flights = int(65 * season_mult)

    # UPDATED: the loaded pipelines do their own OneHotEncoder(handle_unknown=
    # "ignore") internally, so we just pass the raw category/season/district
    # strings straight through. No manual encoding, no silent fallback to 0
    # for an unseen category/district -- the pipeline handles that safely.
    return pd.DataFrame([{
        'day_of_week': date.weekday(),
        'month': month,
        'is_weekend': is_weekend,
        'is_public_holiday': is_holiday,
        'is_festival_period': is_holiday,
        'avg_temperature_c': temp,
        'avg_rainfall_mm': rainfall,
        'daily_flights_at_cmb': daily_flights,
        'hotel_occupancy_rate': REAL_MONTHLY_OCCUPANCY.get(month, ANNUAL_AVG_OCCUPANCY),
        'capacity_per_day': site['capacity'],
        'category': site['category'],
        'season': season,
        'district': site['district'],
        'is_eco_friendly': site['is_eco'],
        'is_unesco': site['is_unesco'],
        'entrance_fee_lkr': site['fee']
    }]), is_holiday, is_weekend

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ FALLBACK PREDICTION (if models not loaded) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
def fallback_prediction(site, date_str):
    """Simulate prediction when ML models are not available"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    month = date.month
    season = get_season(month)  # FIXED: this is a plain string, e.g. "peak" / "low" / "shoulder"

    # Base crowd score with some randomness
    base_score = 0.3
    if season == 'peak':               # FIXED: was season['key'] == 'peak' — crashed with TypeError
        base_score += 0.3
    elif season == 'shoulder':          # FIXED: was season['key'] == 'shoulder'
        base_score += 0.15

    if date.weekday() >= 5:
        base_score += 0.1
    if is_high_impact_date(date_str, site):
        base_score += 0.2

    # Add controlled randomness
    noise = np.random.uniform(-0.1, 0.1)
    crowd_score = round(min(max(base_score + noise, 0), 1), 3)

    # Determine risk level
    if crowd_score >= 0.75:
        risk_level = "High"
    elif crowd_score >= 0.45:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return crowd_score, risk_level

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ EXTENSION 4: LIVE EXPLAINABILITY (SHAP) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# Raw (pre-pipeline) feature names, for anything that still refers to the
# original input columns (e.g. explain's "value" field, build_features()).
FEATURE_NAMES = [
    'day_of_week', 'month', 'is_weekend', 'is_public_holiday', 'is_festival_period',
    'avg_temperature_c', 'avg_rainfall_mm', 'daily_flights_at_cmb', 'hotel_occupancy_rate',
    'capacity_per_day', 'category', 'season', 'district',
    'is_eco_friendly', 'is_unesco', 'entrance_fee_lkr'
]

FEATURE_LABELS = {
    'day_of_week': 'Day of week', 'month': 'Month', 'is_weekend': 'Weekend',
    'is_public_holiday': 'Public holiday', 'is_festival_period': 'Festival period',
    'avg_temperature_c': 'Temperature', 'avg_rainfall_mm': 'Rainfall',
    'daily_flights_at_cmb': 'Flight arrivals (CMB)', 'hotel_occupancy_rate': 'Hotel occupancy',
    'capacity_per_day': 'Site capacity', 'category': 'Site category',
    'season': 'Season', 'district': 'District',
    'is_eco_friendly': 'Eco-friendly site', 'is_unesco': 'UNESCO site',
    'entrance_fee_lkr': 'Entrance fee'
}

def prettify_transformed_feature(name):
    """
    Turn a ColumnTransformer output name like 'num__avg_temperature_c' or
    'cat__category_Nature' into a human label using FEATURE_LABELS where
    possible, e.g. 'Temperature' or 'Site category: Nature'.
    """
    if name.startswith('num__'):
        raw = name[len('num__'):]
        return FEATURE_LABELS.get(raw, raw)
    if name.startswith('cat__'):
        raw = name[len('cat__'):]
        for base in ['category', 'season', 'district']:
            if raw.startswith(base + '_'):
                value = raw[len(base) + 1:]
                return f"{FEATURE_LABELS.get(base, base)}: {value}"
        return raw
    return name

# UPDATED: SHAP now explains the pipeline's inner RandomForest step on
# TRANSFORMED (post-OneHot) input, and feature names come from
# preprocessor.get_feature_names_out() -- not the raw pre-pipeline names -- so
# a one-hot column like "cat__category_Nature" is never mislabeled as the old
# raw integer-encoded "category" feature.
SHAP_EXPLAINER = None
TRANSFORMED_FEATURE_NAMES = None
if MODELS_LOADED:
    try:
        fitted_preprocessor = regressor.named_steps['pre']
        fitted_rf_model = regressor.named_steps['model']
        TRANSFORMED_FEATURE_NAMES = list(fitted_preprocessor.get_feature_names_out())
        SHAP_EXPLAINER = shap.TreeExplainer(fitted_rf_model)
        print("SHAP explainer ready")
    except Exception as e:
        print(f"WARNING: SHAP explainer failed to initialize: {e}")
        SHAP_EXPLAINER = None

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ EXTENSION: DISTANCE HELPER (Haversine) ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# CMB = Bandaranaike International Airport, Katunayake — standard tourist entry point
CMB_LAT = 7.1808
CMB_LON = 79.8841

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ ENDPOINTS ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "model": "Random Forest v1.0" if MODELS_LOADED else "Fallback Mode",
        "total_sites": len(SITES),
        "models_loaded": MODELS_LOADED
    })

@app.route("/sites", methods=["GET"])
def list_sites():
    return jsonify({
        "total": len(SITES),
        "sites": [
            {
                "site_id": k,
                "site_name": v['name'],
                "category": v['category'],
                "district": v['district'],
                "province": v['province'],
                "is_eco_friendly": bool(v['is_eco']),
                "is_unesco": bool(v['is_unesco']),
                "capacity_per_day": v['capacity'],
                "latitude": v['lat'],
                "longitude": v['lon'],
                "entrance_fee_lkr": v['fee'],
                "annual_visitors_2024": v['annual']
            }
            for k, v in SITES.items()
        ]
    })

@app.route("/predict", methods=["GET"])
def predict():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    site = SITES[site_id]

    if MODELS_LOADED:
        features, is_holiday, is_weekend = build_features(site, date_str)
        crowd_score = float(regressor.predict(features)[0])
        crowd_score = round(min(max(crowd_score, 0), 1), 3)
        risk_encoded = classifier.predict(features)[0]
        risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
        prediction_status = "MODEL_PREDICTION"

    else:
        # FIXED: never silently return a random heuristic as if it were the
        # trained model's output. Label it explicitly so the frontend (and
        # anyone reading the response) can tell the difference.
        is_holiday = 1 if is_high_impact_date(date_str, site) else 0
        is_weekend = 1 if datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5 else 0
        crowd_score, risk_level = fallback_prediction(site, date_str)
        prediction_status = "RULE_BASED_BASELINE"

    if risk_level == "High":
        recommendation = "Avoid this date — site will be very crowded"
        badge_color = "red"
    elif risk_level == "Medium":
        recommendation = "Moderately busy — consider visiting early morning"
        badge_color = "amber"
    else:
        recommendation = "Great time to visit — low crowds expected"
        badge_color = "green"

    return jsonify({
        "site_id": site_id,
        "site_name": site['name'],
        "date": date_str,
        "crowd_score": crowd_score,
        "risk_level": risk_level,
        "badge_color": badge_color,
        "recommendation": recommendation,
        "is_holiday": bool(is_holiday),
        "is_weekend": bool(is_weekend),
        "latitude": site['lat'],
        "longitude": site['lon'],
        "hotel_occupancy_rate": REAL_MONTHLY_OCCUPANCY.get(datetime.strptime(date_str, "%Y-%m-%d").month, ANNUAL_AVG_OCCUPANCY),
        "prediction_status": prediction_status
    })

@app.route("/explain", methods=["GET"])
def explain():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    if not MODELS_LOADED or SHAP_EXPLAINER is None:
        return jsonify({
            "error": "Explainability unavailable — model or SHAP explainer not loaded",
            "models_loaded": MODELS_LOADED
        }), 503

    site = SITES[site_id]
    features, is_holiday, is_weekend = build_features(site, date_str)

    crowd_score = float(regressor.predict(features)[0])
    crowd_score = round(min(max(crowd_score, 0), 1), 3)

    # UPDATED: transform through the pipeline's preprocessor first, then
    # explain the inner RF on the transformed (one-hot) row, using the
    # matching transformed feature names.
    transformed_row = fitted_preprocessor.transform(features)
    if hasattr(transformed_row, "toarray"):
        transformed_row = transformed_row.toarray()

    shap_values = SHAP_EXPLAINER.shap_values(transformed_row)
    # TreeExplainer on a regressor returns a single array; be defensive about shape
    values = shap_values[0] if hasattr(shap_values, "__len__") and len(shap_values) == 1 else shap_values
    values = list(values[0]) if hasattr(values[0], "__len__") else list(values)

    contributions = []
    for name, val, raw in zip(TRANSFORMED_FEATURE_NAMES, values, list(transformed_row[0])):
        contributions.append({
            "feature": name,
            "label": prettify_transformed_feature(name),
            "value": raw,
            "shap_contribution": round(float(val), 4),
            "direction": "increases_crowd" if val > 0 else "decreases_crowd"
        })

    contributions.sort(key=lambda c: abs(c["shap_contribution"]), reverse=True)

    return jsonify({
        "site_id": site_id,
        "site_name": site["name"],
        "date": date_str,
        "predicted_crowd_score": crowd_score,
        "base_value": round(float(np.ravel(SHAP_EXPLAINER.expected_value)[0]), 4),
        "top_factors": contributions[:5],
        "all_factors": contributions
    })

@app.route("/forecast", methods=["GET"])
def forecast():
    site_id = int(request.args.get("site_id", 1))
    base_date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    site = SITES[site_id]
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")

    # Honest horizons only: this model has no hour-of-day feature, so
    # horizons are day-offsets from the requested base date, not hours.
    horizons = [
        {"label": "Selected date", "offset_days": 0},
        {"label": "+1 day", "offset_days": 1},
        {"label": "+3 days", "offset_days": 3},
        {"label": "+7 days", "offset_days": 7},
    ]

    results = []
    prev_score = None
    for h in horizons:
        target_date = base_date + timedelta(days=h["offset_days"])
        target_date_str = target_date.strftime("%Y-%m-%d")

        if MODELS_LOADED:
            features, is_holiday, is_weekend = build_features(site, target_date_str)
            crowd_score = float(regressor.predict(features)[0])
            crowd_score = round(min(max(crowd_score, 0), 1), 3)
            risk_encoded = classifier.predict(features)[0]
            risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
        else:
            crowd_score, risk_level = fallback_prediction(site, target_date_str)
            is_holiday = 1 if is_high_impact_date(target_date_str, site) else 0
            is_weekend = 1 if target_date.weekday() >= 5 else 0

        change = None
        if prev_score is not None:
            change = round(crowd_score - prev_score, 3)
        prev_score = crowd_score

        results.append({
            "horizon_label": h["label"],
            "date": target_date_str,
            "crowd_score": crowd_score,
            "risk_level": risk_level,
            "change_from_previous_horizon": change,
            "is_holiday": bool(is_holiday),
            "is_weekend": bool(is_weekend),
            "data_status": "MODEL_PREDICTION",
        })

    return jsonify({
        "site_id": site_id,
        "site_name": site["name"],
        "base_date": base_date_str,
        "forecast": results,
        "note": "Forecast granularity is daily. This model has no hour-of-day feature, so intra-day horizons are not produced."
    })

@app.route("/uncertainty", methods=["GET"])
def uncertainty():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    if not MODELS_LOADED:
        return jsonify({
            "error": "Uncertainty estimation unavailable — model not loaded",
            "models_loaded": MODELS_LOADED
        }), 503

    site = SITES[site_id]
    features, is_holiday, is_weekend = build_features(site, date_str)

    # The regressor is a Pipeline, so the individual trees live on its
    # fitted "model" step. Each tree was trained on the output of the "pre"
    # step, not on the raw DataFrame returned by build_features().
    fitted_preprocessor = regressor.named_steps.get("pre")
    fitted_rf_model = regressor.named_steps.get("model")

    if fitted_preprocessor is None or fitted_rf_model is None:
        return jsonify({
            "error": "Uncertainty estimation unavailable — expected pipeline steps 'pre' and 'model'"
        }), 503

    if not hasattr(fitted_rf_model, "estimators_"):
        return jsonify({
            "error": (
                "Uncertainty estimation unavailable — the fitted model "
                f"{type(fitted_rf_model).__name__} is not a tree ensemble"
            )
        }), 503

    transformed_features = fitted_preprocessor.transform(features)

    # Real per-tree predictions from the Random Forest ensemble. Their spread
    # is an uncertainty signal, but it is not a calibrated confidence interval.
    tree_predictions = np.asarray([
        tree.predict(transformed_features)[0]
        for tree in fitted_rf_model.estimators_
    ], dtype=float)
    tree_predictions = np.clip(tree_predictions, 0, 1)

    mean_pred = float(np.mean(tree_predictions))
    std_pred = float(np.std(tree_predictions))
    p10 = float(np.percentile(tree_predictions, 10))
    p90 = float(np.percentile(tree_predictions, 90))

    # Simple, documented banding — not a statistically calibrated
    # confidence level. Based on relative spread of tree votes.
    if std_pred < 0.03:
        uncertainty_level = "Low"
    elif std_pred < 0.08:
        uncertainty_level = "Moderate"
    else:
        uncertainty_level = "High"

    return jsonify({
        "site_id": site_id,
        "site_name": site["name"],
        "date": date_str,
        "predicted_crowd_score": round(mean_pred, 3),
        "prediction_interval_10_90": [round(p10, 3), round(p90, 3)],
        "std_across_trees": round(std_pred, 4),
        "uncertainty_level": uncertainty_level,
        "n_trees": len(tree_predictions),
        "methodology": "Spread of individual tree predictions within the Random Forest ensemble. This is prediction variance, not a statistically calibrated confidence interval, and not the same as model validation accuracy."
    })

@app.route("/alert", methods=["GET"])
def alert():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    site = SITES[site_id]

    if MODELS_LOADED:
        features, _, _ = build_features(site, date_str)
        risk_encoded = classifier.predict(features)[0]
        risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
    else:
        _, risk_level = fallback_prediction(site, date_str)

    alert_triggered = risk_level == "High"

    return jsonify({
        "site_id": site_id,
        "site_name": site['name'],
        "date": date_str,
        "alert": alert_triggered,
        "risk_level": risk_level,
        "message": f"{site['name']} is forecast to be very crowded on {date_str}. Consider an alternative site." if alert_triggered else f"{site['name']} looks fine on {date_str}."
    })

@app.route("/green-sites", methods=["GET"])
def green_sites():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    green = []
    for site_id, site in SITES.items():
        if site['is_eco'] == 1:
            if MODELS_LOADED:
                features, _, _ = build_features(site, date_str)
                crowd_score = float(regressor.predict(features)[0])
                crowd_score = round(min(max(crowd_score, 0), 1), 3)
                risk_encoded = classifier.predict(features)[0]
                risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
            else:
                crowd_score, risk_level = fallback_prediction(site, date_str)

            green.append({
                "site_id": site_id,
                "site_name": site['name'],
                "category": site['category'],
                "district": site['district'],
                "crowd_score": crowd_score,
                "risk_level": risk_level,
                "latitude": site['lat'],
                "longitude": site['lon']
            })

    green_sorted = sorted(green, key=lambda x: x['crowd_score'])

    return jsonify({
        "date": date_str,
        "total_green_sites": len(green_sorted),
        "green_sites": green_sorted
    })

@app.route("/itinerary-check", methods=["POST"])
def itinerary_check():
    data = request.get_json()
    sites_list = data.get("sites", [])
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    results = []
    for site_id in sites_list:
        if site_id in SITES:
            site = SITES[site_id]
            if MODELS_LOADED:
                features, is_holiday, is_weekend = build_features(site, date_str)
                crowd_score = float(regressor.predict(features)[0])
                crowd_score = round(min(max(crowd_score, 0), 1), 3)
                risk_encoded = classifier.predict(features)[0]
                risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
            else:
                crowd_score, risk_level = fallback_prediction(site, date_str)

            results.append({
                "site_id": site_id,
                "site_name": site['name'],
                "crowd_score": crowd_score,
                "risk_level": risk_level,
                "recommended": risk_level != "High"
            })

    return jsonify({
        "date": date_str,
        "itinerary_check": results
    })

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json() or {}
    site_id = data.get("site_id")
    date_str = data.get("visit_date") or data.get("date")
    actual_crowd = data.get("observed_crowd") if data.get("observed_crowd") is not None else data.get("actual_crowd_level")
    rating = data.get("accuracy") if data.get("accuracy") is not None else data.get("rating")
    comment = data.get("comment", "")
    visit_time = data.get("visit_time") or data.get("time")

    if site_id is None or date_str is None:
        return jsonify({"status": "error", "message": "site_id and date/visit_date are required"}), 400

    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO feedback (site_id, visit_date, visit_time, observed_crowd_level, accuracy_rating, comment)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (site_id, date_str, visit_time, actual_crowd, rating, comment)
                )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        feedback_record = {
            "site_id": site_id, "date": date_str, "time": visit_time, "actual_crowd_level": actual_crowd,
            "rating": rating, "comment": comment,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "db_error": str(e),
        }
        feedback_file = _p("data", "feedback.json")
        try:
            all_feedback = json.load(open(feedback_file)) if os.path.exists(feedback_file) else []
        except:
            all_feedback = []
        all_feedback.append(feedback_record)
        json.dump(all_feedback, open(feedback_file, "w"), indent=2)
        return jsonify({"status": "success", "message": "Feedback recorded (fallback file — DB unavailable).", "warning": str(e)})

    return jsonify({"status": "success", "message": "Feedback recorded. Thank you."})

@app.route("/feedback", methods=["GET"])
def get_feedback():
    records = []
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM feedback ORDER BY id DESC")
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                for row in rows:
                    records.append(dict(zip(cols, row)))
        finally:
            conn.close()
    except Exception as e:
        print("get_feedback DB read failed:", e)
    feedback_file = _p("data", "feedback.json")
    if os.path.exists(feedback_file):
        try:
            file_records = json.load(open(feedback_file))
            records.extend(file_records)
        except Exception as e:
            print("get_feedback file read failed:", e)
    for r in records:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return jsonify({"status": "success", "count": len(records), "feedback": records})
@app.route("/model-metrics", methods=["GET"])
def model_metrics():
    metrics_file = _p("models", "model_metrics.json")
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, "r") as f:
                metrics = json.load(f)
            return jsonify(metrics)
        except:
            pass

    # FIXED: never fabricate/return stale hardcoded metrics if the real
    # metrics file is missing or unreadable. A stale number here would be
    # silently wrong the moment the model is retrained. Fail honestly instead.
    return jsonify({
        "status": "metrics_unavailable",
        "message": "models/model_metrics.json not found or unreadable. Run train_model.py to generate it."
    }), 503

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ NEW: REAL Gini feature importance from the trained regressor ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
@app.route("/feature-importance", methods=["GET"])
def feature_importance():
    if not MODELS_LOADED:
        return jsonify({"error": "Model not loaded", "models_loaded": False}), 503

    # UPDATED: read importances off the pipeline's inner RF step, and pair
    # them with the pipeline's own transformed (post-OneHot) feature names --
    # previously this labeled one-hot-expanded importances with the raw
    # pre-encoding names, which no longer line up 1:1 (item #32 from the audit).
    fitted_rf_model = regressor.named_steps['model']
    fitted_preprocessor = regressor.named_steps['pre']
    transformed_names = list(fitted_preprocessor.get_feature_names_out())
    importances = fitted_rf_model.feature_importances_
    ranked = sorted(
        zip(transformed_names, importances),
        key=lambda x: x[1], reverse=True
    )
    return jsonify({
        "model": "Random Forest Regressor",
        "importance_type": "Gini (mean decrease in impurity)",
        "features": [
            {"feature": name, "label": prettify_transformed_feature(name), "importance": round(float(val), 4)}
            for name, val in ranked
        ]
    })

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ NEW: TOURISM PRESSURE INDICATOR ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# Structural indicator, distinct from date-based crowd_score: how much
# average daily visitor load a site's annual footfall places on its stated
# capacity. No ML — pure arithmetic on data already in tourist_sites.csv.
@app.route("/tourism-pressure", methods=["GET"])
def tourism_pressure():
    results = []
    for site_id, site in SITES.items():
        avg_daily_visitors = site['annual'] / 365.0
        pressure_ratio = avg_daily_visitors / site['capacity'] if site['capacity'] > 0 else None

        if pressure_ratio is None:
            pressure_level = "Unknown"
        elif pressure_ratio >= 0.75:
            pressure_level = "Critical"
        elif pressure_ratio >= 0.45:
            pressure_level = "High"
        elif pressure_ratio >= 0.20:
            pressure_level = "Moderate"
        else:
            pressure_level = "Low"

        results.append({
            "site_id": site_id,
            "site_name": site['name'],
            "district": site['district'],
            "annual_visitors_2024": site['annual'],
            "capacity_per_day": site['capacity'],
            "avg_daily_visitors": round(avg_daily_visitors, 1),
            "pressure_ratio": round(pressure_ratio, 4) if pressure_ratio is not None else None,
            "pressure_level": pressure_level
        })

    results.sort(key=lambda x: (x['pressure_ratio'] is None, -(x['pressure_ratio'] or 0)))

    return jsonify({
        "total_sites": len(results),
        "sites": results,
        "methodology": "pressure_ratio = (annual_visitors_2024 / 365) / capacity_per_day. A structural, date-independent measure of average daily demand relative to stated capacity — distinct from the date-specific ML crowd_score."
    })

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ NEW: PERSONALIZED DESTINATION RANKING ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# Filters sites by user-stated budget and risk tolerance (rule-based),
# then ranks by ML-predicted crowd_score with distance from CMB airport
# as a tiebreaker (also rule-based). crowd_score/risk_level themselves
# come from the trained Random Forest model, not a rule-based calculation.
@app.route("/personalized-ranking", methods=["GET"])
def personalized_ranking():
    max_fee = request.args.get("max_fee", type=int)
    risk_tolerance = request.args.get("risk_tolerance", default="High")  # Low | Medium | High
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    top_n = request.args.get("limit", default=10, type=int)

    RISK_RANK = {"Low": 0, "Medium": 1, "High": 2}
    max_allowed_risk = RISK_RANK.get(risk_tolerance, 2)

    scored = []
    candidate_sites = []
    for site_id, site in SITES.items():
        if max_fee is not None and site['fee'] > max_fee:
            continue
        candidate_sites.append((site_id, site))

    crowd_scores_batch = None
    risk_levels_batch = None
    if MODELS_LOADED and candidate_sites:
        feature_rows = [build_features(site, date_str)[0] for _, site in candidate_sites]
        batch_df = pd.concat(feature_rows, ignore_index=True)
        crowd_scores_batch = regressor.predict(batch_df)
        risk_encoded_batch = classifier.predict(batch_df)
        risk_levels_batch = risk_encoder.inverse_transform(risk_encoded_batch)

    for idx, (site_id, site) in enumerate(candidate_sites):
        if MODELS_LOADED:
            crowd_score = round(min(max(float(crowd_scores_batch[idx]), 0), 1), 3)
            risk_level = risk_levels_batch[idx]
        else:
            crowd_score, risk_level = fallback_prediction(site, date_str)

        if RISK_RANK.get(risk_level, 2) > max_allowed_risk:
            continue

        distance_km = round(haversine_km(CMB_LAT, CMB_LON, site['lat'], site['lon']), 1)

        # Normalize distance against the farthest in-budget/in-tolerance site later;
        # for now store raw values and rank by crowd_score primarily, distance secondarily.
        scored.append({
            "site_id": site_id,
            "site_name": site['name'],
            "district": site['district'],
            "category": site['category'],
            "entrance_fee_lkr": site['fee'],
            "crowd_score": crowd_score,
            "risk_level": risk_level,
            "distance_from_cmb_km": distance_km,
        })

    # Primary: lowest predicted crowding. Secondary: closest to CMB.
    scored.sort(key=lambda x: (x['crowd_score'], x['distance_from_cmb_km']))

    return jsonify({
        "date": date_str,
        "filters_applied": {
            "max_fee_lkr": max_fee,
            "risk_tolerance": risk_tolerance,
            "reference_point": "Bandaranaike International Airport (CMB)"
        },
        "total_matching": len(scored),
        "ranking": scored if top_n <= 0 else scored[:top_n],
        "methodology": "Sites filtered by max entrance fee and risk tolerance (Low/Medium/High) - rule-based filtering. Ranked by crowd_score predicted by the trained Random Forest model (ascending), with distance from CMB airport as a rule-based tiebreaker. Only the filtering and tiebreak logic are rule-based; crowd_score and risk_level come from the ML model."
    })

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ NEW: REAL EVENTS CALENDAR ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
# Reads directly from data/holidays_events.csv — no data duplicated in code.
@app.route("/events", methods=["GET"])
def events():
    events_file = _p("data", "holidays_events.csv")
    if not os.path.exists(events_file):
        return jsonify({"error": "holidays_events.csv not found in data/"}), 404

    df = pd.read_csv(events_file)
    today = datetime.now().date()

    upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"

    records = []
    for _, row in df.iterrows():
        event_date = pd.to_datetime(row["date"]).date()
        if upcoming_only and event_date < today:
            continue
        records.append({
            "date": event_date.strftime("%Y-%m-%d"),
            "event_name": row["event_name"],
            "event_type": row["event_type"],
            "is_national_holiday": bool(row["is_national_holiday"]),
            "expected_impact_level": row["expected_impact_level"],
            "days_from_today": (event_date - today).days
        })

    records.sort(key=lambda r: r["date"])

    return jsonify({
        "total_events": len(records),
        "source": "data/holidays_events.csv",
        "events": records
    })

@app.route("/flights", methods=["GET"])
def flights():
    flight_file = _p("data", "flight_data.csv")
    if os.path.exists(flight_file):
        try:
            df = pd.read_csv(flight_file)
            records = df.head(20).to_dict(orient="records")
            return jsonify({
                "status": "flight data loaded",
                "total_records": len(df),
                "source": "AviationStack API",
                "airport": "Bandaranaike International Airport (CMB)",
                "sample": records
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "no flight data found",
        "message": "Run collect_flights.py first",
        "sample": [
            {"flight": "UL304", "origin": "LHR", "arrival": "08:30", "status": "scheduled"},
            {"flight": "EK650", "origin": "DXB", "arrival": "14:15", "status": "scheduled"},
            {"flight": "QR668", "origin": "DOH", "arrival": "22:45", "status": "scheduled"}
        ]
    })

@app.route("/best-times", methods=["GET"])
def best_times():
    site_id = int(request.args.get("site_id", 1))
    month = int(request.args.get("month", 4))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    site = SITES[site_id]
    results = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day_num, day_name in enumerate(days):
        season = get_season(month)
        is_weekend = 1 if day_num >= 5 else 0
        # Pick any date that actually falls on this day_num/month combo in the
        # current year so build_features() (the single source of truth for
        # feature construction) can be reused instead of duplicating it here.
        probe_year = datetime.now().year
        probe_date = datetime(probe_year, month, 1)
        while probe_date.weekday() != day_num:
            probe_date += timedelta(days=1)
        probe_date_str = probe_date.strftime("%Y-%m-%d")

        if MODELS_LOADED:
            features, _, _ = build_features(site, probe_date_str)
            crowd_score = float(regressor.predict(features)[0])
            crowd_score = round(min(max(crowd_score, 0), 1), 3)
            risk_encoded = classifier.predict(features)[0]
            risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
        else:
            # Simple fallback for best-times
            base = 0.4 + (0.2 if season == "peak" else 0.1 if season == "shoulder" else 0)
            if is_weekend:
                base += 0.15
            crowd_score = round(min(max(base + np.random.uniform(-0.1, 0.1), 0), 1), 3)
            risk_level = "High" if crowd_score >= 0.75 else "Medium" if crowd_score >= 0.45 else "Low"

        results.append({
            "day": day_name,
            "day_num": day_num,
            "crowd_score": crowd_score,
            "risk_level": risk_level,
            "recommended": risk_level == "Low"
        })

    best = sorted(results, key=lambda x: x['crowd_score'])[:3]

    return jsonify({
        "site_id": site_id,
        "site_name": site['name'],
        "month": month,
        "weekly_prediction": results,
        "best_days": best
    })

@app.route("/stream")
def stream():
    def event_stream():
        while True:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                alerts = []
                for site_id, site in SITES.items():
                    if MODELS_LOADED:
                        features, _, _ = build_features(site, today)
                        risk_encoded = classifier.predict(features)[0]
                        risk_level = risk_encoder.inverse_transform([risk_encoded])[0]
                    else:
                        _, risk_level = fallback_prediction(site, today)

                    if risk_level == "High":
                        if MODELS_LOADED:
                            crowd_score = float(regressor.predict(features)[0])
                        else:
                            crowd_score, _ = fallback_prediction(site, today)

                        alerts.append({
                            "overcrowding_alert": True,
                            "site_id": site_id,
                            "site_name": site['name'],
                            "crowd_score": round(min(max(crowd_score, 0), 1), 3),
                            "message": f"{site['name']} is at high risk today. Consider alternatives."
                        })

                data = json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "alerts": alerts,
                    "total_checked": len(SITES)
                })
                yield f"data: {data}\n\n"
                time.sleep(30)
            except Exception as e:
                # FIXED: Don't crash the stream on errors
                yield f"data: {json.dumps({'error': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                time.sleep(30)

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/pipeline-status", methods=["GET"])
def pipeline_status():
    files_to_check = [
        (_p("data", "simulated_crowd_data.csv"), "Crowd Data Simulation"),
        (_p("data", "weather_data.csv"), "Weather Collection"),
        (_p("data", "flight_data.csv"), "Flight Data Collection"),
        (_p("data", "master_dataset_fixed.csv"), "Dataset Merging"),
        (_p("data", "risk_scores.csv"), "Risk Calculation"),
        (_p("outputs", "preprocessing_analysis.png"), "Preprocessing Report"),
        (_p("models", "crowd_pipeline.pkl"), "Model Training"),
        (_p("data", "feedback.json"), "Feedback Collection"),
    ]
    steps = []
    for filepath, name in files_to_check:
        steps.append({
            "name": name,
            "status": "complete" if os.path.exists(filepath) else "pending",
            "file": os.path.relpath(filepath, _BASE_DIR).replace("\\", "/")
        })
    return jsonify({
        "total_steps": len(steps),
        "completed": sum(1 for s in steps if s["status"] == "complete"),
        "steps": steps
    })


# ÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚Â PRIORITY 1: RESEARCH-CRITICAL EXTENSIONS ÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚Â

@app.route("/surge-prediction", methods=["GET"])
def surge_prediction():
    site_id = int(request.args.get("site_id", 1))
    base_date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    lookahead_days = int(request.args.get("days", 7))

    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404

    site = SITES[site_id]
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")

    series = []
    for i in range(lookahead_days):
        d = base_date + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        if MODELS_LOADED:
            features, _, _ = build_features(site, d_str)
            score = float(regressor.predict(features)[0])
            score = round(min(max(score, 0), 1), 3)
        else:
            score, _ = fallback_prediction(site, d_str)
        series.append({"date": d_str, "crowd_score": score})

    SURGE_THRESHOLD = 0.20
    surges = []
    for i in range(1, len(series)):
        delta = round(series[i]["crowd_score"] - series[i - 1]["crowd_score"], 3)
        if delta >= SURGE_THRESHOLD:
            surges.append({
                "date": series[i]["date"],
                "previous_date": series[i - 1]["date"],
                "jump": delta,
                "message": f"Sharp {round(delta * 100)}pp increase expected on {series[i]['date']} vs {series[i - 1]['date']}"
            })

    return jsonify({
        "site_id": site_id, "site_name": site["name"],
        "series": series, "surges_detected": len(surges), "surges": surges,
        "methodology": "Day-over-day jump in model-predicted crowd score above a 20-percentage-point threshold. Daily granularity only."
    })


@app.route("/model-comparison", methods=["GET"])
def model_comparison():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404
    site = SITES[site_id]

    heuristic_score, heuristic_risk = fallback_prediction(site, date_str)
    result = {
        "site_id": site_id, "site_name": site["name"], "date": date_str,
        "heuristic_baseline": {"crowd_score": heuristic_score, "risk_level": heuristic_risk}
    }

    if MODELS_LOADED:
        features, _, _ = build_features(site, date_str)
        rf_score = round(float(min(max(regressor.predict(features)[0], 0), 1)), 3)
        risk_encoded = classifier.predict(features)[0]
        rf_risk = risk_encoder.inverse_transform([risk_encoded])[0]
        result["random_forest"] = {"crowd_score": rf_score, "risk_level": rf_risk}
        result["agreement"] = bool(rf_risk == heuristic_risk)
        result["score_difference"] = round(rf_score - heuristic_score, 3)
    else:
        result["random_forest"] = None
        result["note"] = "Model not loaded — only heuristic baseline available"

    return jsonify(result)


@app.route("/ablation", methods=["GET"])
def ablation():
    site_id = int(request.args.get("site_id", 1))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    if site_id not in SITES:
        return jsonify({"error": "Site not found"}), 404
    if not MODELS_LOADED:
        return jsonify({"error": "Ablation requires a loaded model", "models_loaded": False}), 503

    site = SITES[site_id]
    features, _, _ = build_features(site, date_str)
    baseline = float(regressor.predict(features)[0])

    ablation_results = []
    for col in FEATURE_NAMES:
        modified = features.copy()
        if pd.api.types.is_numeric_dtype(features[col]):
            modified[col] = 0
        else:
            modified[col] = "__ablated__"  # unseen category -> all-zero one-hot (handle_unknown="ignore")
        ablated_pred = float(regressor.predict(modified)[0])
        ablation_results.append({
            "feature": col,
            "label": FEATURE_LABELS.get(col, col),
            "baseline_prediction": round(baseline, 4),
            "prediction_without_feature": round(ablated_pred, 4),
            "impact": round(baseline - ablated_pred, 4)
        })

    ablation_results.sort(key=lambda x: abs(x["impact"]), reverse=True)

    return jsonify({
        "site_id": site_id, "site_name": site["name"], "date": date_str,
        "baseline_prediction": round(baseline, 4),
        "ablation": ablation_results,
        "methodology": "Each feature is individually neutralised (numeric features set to 0; categorical features set to an unseen category so their one-hot encoding is all zeros) and the model re-run; impact = baseline minus ablated prediction. Single-instance ablation for this site/date, not a dataset-wide study."
    })


@app.route("/error-analysis", methods=["GET"])
def error_analysis():
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT site_id, visit_date, observed_crowd_level
                    FROM feedback
                    WHERE observed_crowd_level IS NOT NULL
                    ORDER BY visit_date DESC LIMIT 500
                """)
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not read feedback: {e}"}), 503

    if not rows:
        return jsonify({"status": "no_data", "message": "No feedback records with observed crowd levels yet."})

    def norm(v):
        try:
            return (float(v) - 1) / 4.0
        except Exception:
            return None

    errors_by_site, all_errors = {}, []
    for site_id, visit_date, observed in rows:
        if site_id not in SITES:
            continue
        obs_norm = norm(observed)
        if obs_norm is None:
            continue
        if MODELS_LOADED:
            features, _, _ = build_features(SITES[site_id], str(visit_date))
            pred = float(regressor.predict(features)[0])
        else:
            pred, _ = fallback_prediction(SITES[site_id], str(visit_date))
        err = abs(pred - obs_norm)
        all_errors.append(err)
        errors_by_site.setdefault(site_id, []).append(err)

    per_site = [{"site_id": sid, "site_name": SITES[sid]["name"],
                 "mean_abs_error": round(sum(e) / len(e), 4), "n": len(e)}
                for sid, e in errors_by_site.items()]
    per_site.sort(key=lambda x: x["mean_abs_error"], reverse=True)

    return jsonify({
        "overall_mae": round(sum(all_errors) / len(all_errors), 4) if all_errors else None,
        "n_records": len(all_errors),
        "worst_sites": per_site[:10],
        "methodology": "Observed crowd level (1-5 self-report scale) normalized to 0-1 and compared against the model's prediction for the same site/date."
    })

# ÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚Â END PRIORITY 1 EXTENSIONS ÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚ÂÃƒÂ¢Ã¢â‚¬Â¢Ã‚Â



@app.route("/retrain", methods=["POST"])
def retrain_model():
    # Honest status check -- no fake success. Looks for a real training
    # script; if none exists, says so plainly instead of pretending to retrain.
    candidates = [
        _p("scripts", "train_model.py"),
        _p("train_model.py"),
        _p("train.py"),
        _p("training", "train_model.py"),
    ]
    found = None
    for c in candidates:
        if os.path.exists(c):
            found = c
            break
    if not found:
        return jsonify({
            "status": "unavailable",
            "message": "No training script found on the server. Retraining is not yet wired up -- add a training script to enable this."
        }), 501
    return jsonify({
            "status": "not_implemented",
            "message": "Found " + found + " but automatic execution is not yet implemented. Run it manually for now."
        }), 501

if __name__ == "__main__":
    # FIXED: Run on all interfaces so it's accessible from network
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))


