"""Safety Card: family / home WhatsApp numbers alerted on SOS."""

from flask import Blueprint, jsonify, request

from app.auth_utils import tourist_required
from app.extensions import db
from app.models import FamilyContact, Incident, LocationPing
from app.services.whatsapp import alert_family, normalize_phone

bp = Blueprint("family", __name__, url_prefix="/api/family-contacts")


@bp.get("")
@tourist_required
def list_contacts(tourist):
    return jsonify({"contacts": [c.to_dict() for c in tourist.family_contacts], "max": FamilyContact.MAX_PER_TOURIST})


@bp.post("")
@tourist_required
def add_contact(tourist):
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()[:120]
    phone = normalize_phone(d.get("phone"))
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not phone:
        return jsonify({"error": "Enter the WhatsApp number with country code, e.g. +44 7700 900123"}), 400
    if any(c.phone == phone for c in tourist.family_contacts):
        return jsonify({"error": "This number is already saved"}), 409
    if len(tourist.family_contacts) >= FamilyContact.MAX_PER_TOURIST:
        return jsonify({"error": f"You can save up to {FamilyContact.MAX_PER_TOURIST} numbers"}), 400
    c = FamilyContact(tourist_id=tourist.id, name=name, phone=phone)
    db.session.add(c)
    db.session.commit()
    return jsonify({"contact": c.to_dict()}), 201


@bp.post("/<int:contact_id>/send")
@tourist_required
def send_to_contact(tourist, contact_id):
    """Send this family number the open SOS message and the tourist's current location."""
    contact = FamilyContact.query.get_or_404(contact_id)
    if contact.tourist_id != tourist.id:
        return jsonify({"error": "Forbidden"}), 403
    incident = (Incident.query.filter(Incident.tourist_id == tourist.id,
                                      Incident.status.in_(Incident.OPEN_STATUSES))
                .order_by(Incident.id.desc()).first())
    if not incident:
        return jsonify({"error": "Send SOS first. Then press Send and your message and location go to this family member."}), 400
    data = request.get_json(silent=True) or {}
    lat = lng = None
    try:
        lat, lng = float(data.get("latitude")), float(data.get("longitude"))
    except (TypeError, ValueError):
        lat = lng = None
    if lat is not None:
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return jsonify({"error": "Location could not be read. Turn on location and press Send again."}), 400
        try:
            accuracy = float(data.get("accuracy")) if data.get("accuracy") not in (None, "") else None
        except (TypeError, ValueError):
            accuracy = None
        if accuracy is not None and accuracy > 1000:
            return jsonify({"error": "This location is only a city guess. Turn on precise location and press Send again."}), 400
        db.session.add(LocationPing(incident_id=incident.id, latitude=lat, longitude=lng, accuracy=accuracy))
        db.session.flush()
    result = alert_family(incident, contacts=[contact], lat=lat, lng=lng)
    previous = {row["phone"]: row for row in (incident.family_alerts or {}).get("recipients") or []}
    for row in result["recipients"]:
        previous[row["phone"]] = row
    incident.family_alerts = {
        "recipients": list(previous.values()),
        "delivered": any(row["delivered"] for row in previous.values()),
        "message": result["message"],
    }
    db.session.commit()
    one = result["recipients"][0]
    return jsonify({"delivered": one["delivered"], "whatsapp_link": one["whatsapp_link"],
                    "family_alerts": incident.family_alerts})


@bp.delete("/<int:contact_id>")
@tourist_required
def delete_contact(tourist, contact_id):
    c = FamilyContact.query.get_or_404(contact_id)
    if c.tourist_id != tourist.id:
        return jsonify({"error": "Forbidden"}), 403
    db.session.delete(c)
    db.session.commit()
    return jsonify({"deleted": True})
