"""
Ayurveda & Spiritual Tourism Matching System - Flask API
============================================================
Full backend, synced with the JS reference UI (tour_ceylon_webapp_desktop.html).
Run: python3 app.py -> serves on port 5003

Endpoints:
  GET  /health                  - health check
  GET  /centers?path=ayurveda   - list all centers for a path
  POST /recommend                - main matching endpoint (path, condition, dosha inputs, budget, companion)
  GET  /center/<name>            - full detail for one center (description, duration, outcome, sessions/offers)
  POST /cost-estimate             - trip cost calculator
"""
import os
from flask import Flask, request, jsonify, send_from_directory, session
from matching_engine import (
    predict_dosha, match_centers, get_path_pool, CONDITIONS_BY_PATH,
    get_duration_info, get_outcome_info, get_cost_estimate,
    get_session_schedule, get_ayurveda_offers, detect_risk_flags, POOL,
    save_pool, get_analytics, get_flagged_centers,
    detect_risk_flags_ml, classify_symptom_text, predict_outcome_personalized
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# NOTE: demo-grade auth only - a single shared password, not a real user system.
# Fine for a research prototype / local demo; would need proper auth for production.
ADMIN_PASSWORD = "tourceylon2026"

app = Flask(__name__, static_folder=None)
app.secret_key = "tour-ceylon-fyp-dev-secret-key-change-if-deploying"


def require_admin():
    return session.get("is_admin") is True


@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def serve_frontend_files(filename):
    # Serves css/js/images referenced by index.html (e.g. /css/style.css, /js/app.js, /images/logo.png)
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "centers_loaded": len(POOL)})


@app.route("/api/centers", methods=["GET"])
def list_centers():
    path = request.args.get("path", "ayurveda")
    pool = get_path_pool(path)
    return jsonify({
        "path": path, "count": len(pool),
        "centers": [{"name": c["name"], "category": c["category"], "district": c.get("district")} for c in pool]
    })


@app.route("/api/conditions", methods=["GET"])
def list_conditions():
    path = request.args.get("path", "ayurveda")
    return jsonify({"path": path, "conditions": CONDITIONS_BY_PATH.get(path, [])})


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json(force=True)

    required = ["condition", "age", "gender", "sleep_pattern", "appetite",
                "cold_heat_sensitivity", "emotional_tendency", "budget_tier"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    path = data.get("path", "ayurveda")
    dosha, confidence = predict_dosha(
        data["age"], data["gender"], data["sleep_pattern"],
        data["appetite"], data["cold_heat_sensitivity"], data["emotional_tendency"]
    )

    top_n = data.get("top_n", 6)
    companion_condition = data.get("companion_condition")
    results = match_centers(data["condition"], dosha, data["budget_tier"],
                             top_n=top_n, companion_condition=companion_condition, path=path)

    # Enrich each result with duration/outcome for the queried condition
    duration = get_duration_info(data["condition"])
    outcome = get_outcome_info(data["condition"])

    return jsonify({
        "input": {"condition": data["condition"], "budget_tier": data["budget_tier"], "path": path,
                   "companion_condition": companion_condition},
        "predicted_dosha": dosha,
        "dosha_confidence_pct": confidence,
        "expected_duration": duration,
        "outcome_likelihood": outcome,
        "recommendations": results,
    })


@app.route("/api/match", methods=["POST"])
def match_only():
    """Matching with a KNOWN dosha (no re-prediction) - used by the 'Try a
    Different Scenario' comparison, where the tourist's wellness profile
    (dosha) stays fixed while condition/budget/companion are varied."""
    data = request.get_json(force=True)
    required = ["condition", "dosha", "budget_tier"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    path = data.get("path", "ayurveda")
    top_n = data.get("top_n", 1)
    companion_condition = data.get("companion_condition")
    results = match_centers(data["condition"], data["dosha"], data["budget_tier"],
                             top_n=top_n, companion_condition=companion_condition, path=path)
    return jsonify({"recommendations": results})


@app.route("/api/center/<path:name>", methods=["GET"])
def center_detail(name):
    match = next((c for c in POOL if c["name"].lower() == name.lower()), None)
    if not match:
        return jsonify({"error": "Center not found"}), 404

    result = dict(match)
    result["risk_flags"] = detect_risk_flags(match.get("reviews", []))
    if match["category"] == "Spiritual/Meditation":
        result["session_pattern"] = get_session_schedule(match)
    else:
        result["typical_offers"] = get_ayurveda_offers(match["category"])
    return jsonify(result)


@app.route("/api/cost-estimate", methods=["POST"])
def cost_estimate():
    data = request.get_json(force=True)
    required = ["condition", "price_tier"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    travelers = data.get("travelers", 1)
    est = get_cost_estimate(data["condition"], data["price_tier"], travelers)
    if est is None:
        return jsonify({"error": "No duration data available for this condition"}), 404
    return jsonify(est)


# ============================================================
# ADMIN - serves the admin dashboard + its API (all gated by session auth)
# ============================================================
ADMIN_DIR = os.path.join(FRONTEND_DIR, "admin")


@app.route("/admin", methods=["GET"])
def serve_admin():
    return send_from_directory(ADMIN_DIR, "index.html")


@app.route("/admin/<path:filename>", methods=["GET"])
def serve_admin_files(filename):
    return send_from_directory(ADMIN_DIR, filename)


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True)
    if data.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Incorrect password"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    return jsonify({"ok": True})


@app.route("/api/admin/check", methods=["GET"])
def admin_check():
    return jsonify({"is_admin": require_admin()})


@app.route("/api/admin/centers", methods=["GET"])
def admin_list_centers():
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    return jsonify({"centers": POOL})


@app.route("/api/admin/centers/<int:idx>", methods=["PUT"])
def admin_edit_center(idx):
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    if idx < 0 or idx >= len(POOL):
        return jsonify({"error": "Center not found"}), 404
    data = request.get_json(force=True)
    editable_fields = ["name", "category", "conditions_text", "dosha_focus", "price_tier",
                        "phone", "district", "address", "verified", "notes", "nlp_quality"]
    changed_fields = {}
    for field in editable_fields:
        if field in data:
            POOL[idx][field] = data[field]
            changed_fields[field] = data[field]
    save_pool(changed_idx=idx, changed_fields=changed_fields)
    return jsonify({"ok": True, "center": POOL[idx]})


@app.route("/api/admin/centers", methods=["POST"])
def admin_add_center():
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "Name is required"}), 400
    new_center = {
        "name": data.get("name"), "category": data.get("category", "Curative"),
        "conditions_text": data.get("conditions_text", ""), "dosha_focus": data.get("dosha_focus", "General/Unspecified"),
        "nlp_quality": float(data.get("nlp_quality", 3.5)), "quality_source": "Manually added (admin)",
        "price_tier": data.get("price_tier", "Mid"), "google_rating": None,
        "phone": data.get("phone", ""), "lat": data.get("lat"), "lng": data.get("lng"),
        "reviews": [], "verified": data.get("verified", "Needs verification"), "notes": data.get("notes", ""),
        "address": data.get("address", ""), "district": data.get("district", ""),
        "google_rating_real": None, "review_count_real": None,
    }
    POOL.append(new_center)
    save_pool()
    return jsonify({"ok": True, "center": new_center, "index": len(POOL) - 1})


@app.route("/api/admin/centers/<int:idx>", methods=["DELETE"])
def admin_delete_center(idx):
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    if idx < 0 or idx >= len(POOL):
        return jsonify({"error": "Center not found"}), 404
    removed = POOL.pop(idx)
    save_pool()
    return jsonify({"ok": True, "removed": removed["name"]})


@app.route("/api/admin/flagged-reviews", methods=["GET"])
def admin_flagged_reviews():
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    return jsonify({"flagged": get_flagged_centers()})


@app.route("/api/admin/analytics", methods=["GET"])
def admin_analytics():
    if not require_admin():
        return jsonify({"error": "Not authorized"}), 401
    return jsonify(get_analytics())


@app.route("/api/classify-symptom", methods=["POST"])
def api_classify_symptom():
    """
    Optional free-text symptom entry point. Given a tourist's own
    description ("my knees hurt and I feel stressed"), suggests a
    condition category to pre-fill the dropdown - NOT a replacement
    for the dropdown, an assistive shortcut.

    Body: { "text": "...", "lang": "en"|"de"|"ru"|"zh"|"ja", "domain": "ayurveda"|"spiritual" }
    "lang" selects which of the 5 dedicated per-language models to use
    (each trained on its own native-language example data, not a
    translation layer over a single English model). Defaults to "en".
    "domain" selects which category set to predict from - "ayurveda" (12
    medical/wellness conditions) or "spiritual" (6 meditation/retreat
    types) - these are separate classifiers, not one shared model, since
    the category sets don't overlap at all. Defaults to "ayurveda".
    """
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    domain = data.get("domain", "ayurveda")
    if not text:
        return jsonify({"error": "text is required"}), 400
    return jsonify(classify_symptom_text(text, lang, domain))


@app.route("/api/predict-outcome", methods=["POST"])
def api_predict_outcome():
    """
    Personalized treatment outcome prediction (replaces the static
    per-condition percentage with an age/dosha/duration-aware estimate).
    """
    data = request.get_json(force=True)
    required = ["age", "dosha", "condition", "duration_days"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400
    result = predict_outcome_personalized(data["age"], data["dosha"], data["condition"], data["duration_days"])
    return jsonify(result)


@app.route("/api/safety-check", methods=["POST"])
def api_safety_check():
    """
    Enhanced safety-flag check using both the keyword matcher and the
    trained ML classifier, showing where they agree/disagree for
    transparency (e.g. the keyword matcher's known false-positive on
    'I cannot recommend it highly enough').
    """
    data = request.get_json(force=True)
    reviews = data.get("reviews", [])
    return jsonify({"flags": detect_risk_flags_ml(reviews)})


if __name__ == "__main__":
    print(f"Loaded {len(POOL)} centers. Ready at http://localhost:5003")
    print(f"Admin dashboard: http://localhost:5003/admin")
    app.run(host="0.0.0.0", port=5003, debug=False)
