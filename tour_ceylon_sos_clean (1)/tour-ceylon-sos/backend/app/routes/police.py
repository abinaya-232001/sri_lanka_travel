"""Police dashboard: each station sees only its own incidents."""

from flask import Blueprint, jsonify, request

from app.auth_utils import police_required
from app.extensions import db
from app.models import ChatMessage, Incident
from app.services import realtime
from app.services.immigration_api import ImmigrationApiError, fetch_travellers, visa_rows

bp = Blueprint("police", __name__, url_prefix="/api/police")


@bp.get("/me")
@police_required
def me(officer):
    return jsonify({"username": officer.username, "station": officer.station.to_dict(),
                    "must_change_password": officer.must_change_password})


@bp.get("/incidents")
@police_required
def list_incidents(officer):
    q = Incident.query.filter_by(station_id=officer.station_id)
    if request.args.get("active", "1") != "0":
        q = q.filter(Incident.status.in_(Incident.OPEN_STATUSES))
    return jsonify({"incidents": [i.to_dict(for_police=True) for i in q.order_by(Incident.id.desc()).limit(200)]})


@bp.get("/incidents/<int:incident_id>")
@police_required
def get_incident(officer, incident_id):
    inc = Incident.query.get_or_404(incident_id)
    if inc.station_id != officer.station_id:
        return jsonify({"error": "This incident belongs to another station"}), 403
    return jsonify({"incident": inc.to_dict(for_police=True)})


@bp.post("/incidents/<int:incident_id>/status")
@police_required
def set_status(officer, incident_id):
    inc = Incident.query.get_or_404(incident_id)
    if inc.station_id != officer.station_id:
        return jsonify({"error": "This incident belongs to another station"}), 403
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in Incident.STATUSES:
        return jsonify({"error": f"status must be one of {', '.join(Incident.STATUSES)}"}), 400
    inc.status = status
    if status in ("resolved", "closed"):
        inc.tracking_active = False
    text = {"acknowledged": "👮 Police have seen your SOS.",
            "responding": "🚓 Police are on the way.",
            "resolved": "✅ Police marked this case as resolved.",
            "closed": "Case closed."}.get(status)
    msg = None
    if text:
        msg = ChatMessage(incident_id=inc.id, sender_role="system", kind="text", body=text)
        db.session.add(msg)
    db.session.commit()
    if msg:
        realtime.emit_chat(inc.id, msg.to_dict())
    realtime.emit_incident_update(inc)
    return jsonify({"incident": inc.to_dict(for_police=True)})


@bp.get("/immigration")
@police_required
def immigration_desk(_officer):
    """Visa list from the separate immigration API. Expiring means the visa ends within 14 days."""
    try:
        rows = visa_rows(fetch_travellers())
    except ImmigrationApiError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({
        "source": "immigration_api",
        "records": rows,
        "summary": {
            "expiring": sum(1 for r in rows if r["status"] == "expiring"),
            "over": sum(1 for r in rows if r["status"] == "over"),
            "valid": sum(1 for r in rows if r["status"] == "valid"),
            "departed": sum(1 for r in rows if r["status"] == "departed"),
            "unknown": sum(1 for r in rows if r["status"] == "unknown"),
        },
    })
