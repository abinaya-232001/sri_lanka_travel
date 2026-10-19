"""Immigration integration + visa monitoring APIs."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from app import db
from app.services.audit import log_audit
from app.services.immigration_api_client import api_status, sync_all_tourists, sync_tourist
from app.services.immigration_monitor import (
    LEGAL_LOCATION_NOTE,
    OVERSTAY_LEGAL_NOTE,
    build_integration_record,
    build_summary,
    build_visa_monitoring_card,
    integration_meta,
    sync_alerts_for_police,
)
from app.sos_models import Tourist
from app.sos_models_ext import ImmigrationSafetyAlert

immigration_bp = Blueprint("immigration", __name__, url_prefix="/api/immigration")


def _police_access(claims):
    if claims.get("role") not in {"officer", "supervisor", "admin"}:
        return jsonify({"error": "Officer access required"}), 403
    if claims.get("role") != "admin" and not claims.get("station_id"):
        return jsonify({"error": "Station scope required"}), 403
    return None


def _immigration_access(claims):
    if claims.get("role") not in {"immigration_officer", "admin"}:
        return jsonify({"error": "Immigration authority access required"}), 403
    return None


def _all_tourists():
    return Tourist.query.order_by(Tourist.secure_tourist_id, Tourist.id).all()


@immigration_bp.get("/integration")
@jwt_required()
def immigration_integration():
    """Separate immigration authority dashboard — minimum tourist safety fields only."""
    claims = get_jwt()
    denied = _immigration_access(claims)
    if denied:
        return denied

    tourists = _all_tourists()
    records = [build_integration_record(t) for t in tourists]
    alert_days = request.args.get("days", 30, type=int)
    summary = build_summary(records, alert_days)
    overstays = [r for r in records if r.get("is_overstay_suspected")]

    log_audit("immigration_integration_view", claims.get("role"), None, "immigration", None, str(len(records)))
    db.session.commit()
    return jsonify(
        {
            "integration": integration_meta(authorized=claims.get("role") == "immigration_officer"),
            "summary": summary,
            "records": records,
            "overstay_suspected": overstays,
            "legal_notice": LEGAL_LOCATION_NOTE,
        }
    )


@immigration_bp.get("/visa-monitoring")
@jwt_required()
def visa_monitoring():
    claims = get_jwt()
    if claims.get("role") not in {"immigration_officer", "officer", "supervisor", "admin"}:
        return jsonify({"error": "Authorized access required"}), 403
    if claims.get("role") in {"officer", "supervisor"}:
        denied = _police_access(claims)
        if denied:
            return denied

    cards = [build_visa_monitoring_card(t) for t in _all_tourists()]
    log_audit("immigration_visa_monitoring", claims.get("role"), None, "immigration", None, str(len(cards)))
    db.session.commit()
    return jsonify(
        {
            "cards": cards,
            "legal_notice": LEGAL_LOCATION_NOTE,
            "overstay_policy": OVERSTAY_LEGAL_NOTE,
        }
    )


@immigration_bp.get("/api-status")
@jwt_required()
def immigration_api_status():
    """Is the Department of Immigration API connected?"""
    claims = get_jwt()
    denied = _immigration_access(claims)
    if denied:
        return denied
    return jsonify(api_status())


@immigration_bp.post("/sync-from-api")
@jwt_required()
def sync_from_immigration_api():
    """Pull official visa details for every tourist from the immigration API."""
    claims = get_jwt()
    denied = _immigration_access(claims)
    if denied:
        return denied
    result = sync_all_tourists()
    if not result.get("enabled"):
        return jsonify({**result, "error": "Immigration API is not configured (set IMMIGRATION_API_URL)."}), 503
    log_audit("immigration_api_sync", claims.get("role"), None, "immigration", None, str(result["verified"]))
    db.session.commit()
    return jsonify(result)


@immigration_bp.post("/tourists/<int:tourist_id>/sync")
@jwt_required()
def sync_one_tourist(tourist_id: int):
    claims = get_jwt()
    denied = _immigration_access(claims)
    if denied:
        return denied
    tourist = Tourist.query.get_or_404(tourist_id)
    result = sync_tourist(tourist)
    log_audit("immigration_api_sync_one", claims.get("role"), None, "immigration", tourist.id, result)
    db.session.commit()
    return jsonify({"result": result, "record": build_integration_record(tourist)})


@immigration_bp.post("/sync-alerts")
@jwt_required()
def publish_alerts_to_police():
    """Immigration dashboard publishes visa/overstay alerts to police immigration feed."""
    claims = get_jwt()
    denied = _immigration_access(claims)
    if denied:
        return denied

    alert_days = request.args.get("days", 30, type=int)
    result = sync_alerts_for_police(alert_days=alert_days)
    log_audit("immigration_sync_alerts", claims.get("role"), None, "immigration", None, str(result["open_alerts"]))
    return jsonify(
        {
            "ok": True,
            "message": "Alerts published to police immigration dashboard.",
            **result,
        }
    )


@immigration_bp.get("/police-feed")
@jwt_required()
def police_immigration_feed():
    """Police immigration dashboard — alerts from immigration monitoring + visa cards."""
    claims = get_jwt()
    denied = _police_access(claims)
    if denied:
        return denied

    alert_days = request.args.get("days", 30, type=int)
    sync_alerts_for_police(alert_days=alert_days)

    alerts = (
        ImmigrationSafetyAlert.query.filter_by(status=ImmigrationSafetyAlert.STATUS_OPEN)
        .order_by(ImmigrationSafetyAlert.published_to_police_at.desc())
        .limit(100)
        .all()
    )
    cards = [build_visa_monitoring_card(t) for t in _all_tourists()]
    records = [build_integration_record(t) for t in _all_tourists()]
    summary = build_summary(records, alert_days)

    log_audit("immigration_police_feed", claims.get("role"), None, "immigration", None, str(len(alerts)))
    db.session.commit()
    return jsonify(
        {
            "integration": integration_meta(),
            "summary": summary,
            "alerts": [a.to_dict() for a in alerts],
            "visa_monitoring": cards,
            "overstay_cases": [c for c in cards if c.get("is_overstay_suspected")],
            "legal_notice": LEGAL_LOCATION_NOTE,
            "overstay_policy": OVERSTAY_LEGAL_NOTE,
        }
    )


@immigration_bp.patch("/alerts/<int:alert_id>")
@jwt_required()
def acknowledge_alert(alert_id: int):
    claims = get_jwt()
    denied = _police_access(claims)
    if denied:
        return denied

    alert = ImmigrationSafetyAlert.query.get_or_404(alert_id)
    alert.status = ImmigrationSafetyAlert.STATUS_ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    if claims.get("role") == "officer":
        alert.acknowledged_by_officer_id = int(get_jwt()["sub"])
    db.session.commit()
    return jsonify({"alert": alert.to_dict()})


@immigration_bp.get("/dashboard")
@jwt_required()
def immigration_dashboard_legacy():
    claims = get_jwt()
    denied = _police_access(claims)
    if denied:
        return denied
    response = police_immigration_feed()
    return response


@immigration_bp.get("/visa-monitor")
@jwt_required()
def visa_monitor_legacy():
    claims = get_jwt()
    denied = _police_access(claims)
    if denied:
        return denied

    alert_days = request.args.get("days", 30, type=int)
    records = [build_integration_record(t) for t in _all_tourists()]
    summary = build_summary(records, alert_days)
    threshold_cards = [r for r in records if r.get("visa_valid_to")]
    from datetime import date, timedelta

    threshold = date.today() + timedelta(days=alert_days)
    alerts = [r for r in records if r.get("visa_valid_to") and date.fromisoformat(r["visa_valid_to"]) <= threshold]

    log_audit("immigration_visa_monitor", claims.get("role"), None, "immigration", None, str(len(records)))
    db.session.commit()
    return jsonify(
        {
            "tourists": records,
            "visa_alerts": alerts,
            "alert_count": len(alerts),
            "summary": summary,
            "source": "local_tourist_records",
            "external_provider_verified": False,
        }
    )
