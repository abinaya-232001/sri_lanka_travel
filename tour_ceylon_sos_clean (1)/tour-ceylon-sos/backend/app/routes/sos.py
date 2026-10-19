"""SOS: message/voice -> English -> RF incident type -> nearest station,
tips & contacts, WhatsApp to family, live location until the tourist stops it."""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from app.auth_utils import incident_access, tourist_required
from app.extensions import db
from app.models import ChatMessage, Incident, LocationPing
from app.services import realtime
from app.services.classifier import resolve_incident_type
from app.services.guidance import build_guidance
from app.services.incident_guidance import refresh_guidance_from_message
from app.services.media import absolute, save_upload
from app.services.routing import nearest_station
from app.services.speech import translate_to_english, voice_to_english
from app.services.whatsapp import alert_family

bp = Blueprint("sos", __name__, url_prefix="/api")


def _payload():
    return request.form if request.form else (request.get_json(silent=True) or {})


def _coords(data):
    try:
        lat, lng = float(data.get("latitude")), float(data.get("longitude"))
    except (TypeError, ValueError):
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, None
    return lat, lng


def _understand(tourist, data, incident_id_for_media):
    """Typed text + optional voice note -> original text, English text, language, voice path."""
    lang = (data.get("language") or tourist.language or "en").lower()
    text = (data.get("message") or "").strip()
    voice_path = None
    parts_original, parts_english, ok_all, detected = [], [], True, "en"

    if text:
        # The incident model is trained on English. Plain typed English goes straight to it.
        ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
        if lang.startswith("en") or ascii_ratio > 0.9:
            parts_original.append(text)
            parts_english.append(text)
        else:
            en, detected, ok = translate_to_english(text, "auto")
            parts_original.append(text)
            parts_english.append(en or text)
            ok_all = ok
    voice = request.files.get("voice")
    if voice:
        voice_path, err = save_upload(voice, incident_id_for_media, "voice")
        if voice_path:
            v = voice_to_english(absolute(voice_path), data.get("voice_transcript"), lang)
            if v.get("english"):
                original = (v.get("original") or v["english"]).strip()
                already = " ".join(parts_original)
                if original and original not in already:
                    parts_original.append(original)
                    parts_english.append(v["english"])
                    ok_all = ok_all and v["translated"]
                detected = v.get("language") or detected
    return {
        "original": " ".join(parts_original) or None,
        "english": " ".join(parts_english) or None,
        "language": detected if detected not in ("auto", "") else "en",
        "translated": ok_all,
        "voice_path": voice_path,
    }


def _add_chat(incident, role, kind, body=None, english=None, media=None):
    m = ChatMessage(incident_id=incident.id, sender_role=role, kind=kind, body=body,
                    body_english=english, media_path=media)
    db.session.add(m)
    return m


@bp.post("/sos")
@tourist_required
def create_sos(tourist):
    data = _payload()
    lat, lng = _coords(data)
    if lat is None:
        return jsonify({"error": "Your location is needed to send SOS. Turn on location (GPS) and try again."}), 400
    if _coarse(data):
        return jsonify({"error": "This location is only a city guess. Turn on precise location and try again."}), 400

    open_incident = (Incident.query.filter(Incident.tourist_id == tourist.id,
                                           Incident.status.in_(Incident.OPEN_STATUSES))
                     .order_by(Incident.id.desc()).first())
    if open_incident:
        return _follow_up(open_incident, tourist, data, lat, lng)

    station, dist = nearest_station(lat, lng)
    if not station:
        return jsonify({"error": "No police stations configured"}), 503

    incident = Incident(tourist_id=tourist.id, station_id=station.id, start_lat=lat, start_lng=lng,
                        distance_km=round(dist, 2), tracking_active=True,
                        tracking_events=[{"active": True, "at": datetime.utcnow().isoformat() + "Z", "by": "sos"}])
    db.session.add(incident)
    db.session.flush()  # id for media folder

    u = _understand(tourist, data, incident.id)
    decided, details = resolve_incident_type(u["english"], "other", english=u["translated"])
    incident.incident_type = decided or "other"
    incident.classification = details
    incident.message_original, incident.message_english = u["original"], u["english"]
    incident.original_language = u["language"]
    incident.guidance = build_guidance(incident.incident_type, lat=lat, lng=lng, station=station,
                                       station_distance_km=dist, classification=details)

    db.session.add(LocationPing(incident_id=incident.id, latitude=lat, longitude=lng,
                                accuracy=_float(data.get("accuracy"))))
    _add_chat(incident, "system", "text",
              f"🚨 SOS — {incident.guidance['label']}. Location shared with {station.name}.")
    if (data.get("message") or "").strip():
        _add_chat(incident, "tourist", "text", data["message"].strip(),
                  u["english"] if u["english"] != u["original"] else None)
    if u["voice_path"]:
        _add_chat(incident, "tourist", "voice", data.get("voice_transcript") or None, u["english"], u["voice_path"])
    db.session.commit()

    try:
        incident.family_alerts = alert_family(incident)
    except Exception:
        current_app.logger.exception("WhatsApp family alert failed")
        incident.family_alerts = {"recipients": [], "delivered": False}
    db.session.commit()
    realtime.emit_new_sos(incident)
    return jsonify({"incident": incident.to_dict(), "created": True}), 201


def _follow_up(incident, tourist, data, lat, lng):
    """SOS pressed again while a case is open: the message goes into the same case's chat."""
    u = _understand(tourist, data, incident.id)
    new_msgs = []
    if (data.get("message") or "").strip():
        new_msgs.append(_add_chat(incident, "tourist", "text", data["message"].strip(),
                                  u["english"] if u["english"] != u["original"] else None))
    if u["voice_path"]:
        new_msgs.append(_add_chat(incident, "tourist", "voice", data.get("voice_transcript") or None,
                                  u["english"], u["voice_path"]))
    if incident.tracking_active and not _coarse(data):
        db.session.add(LocationPing(incident_id=incident.id, latitude=lat, longitude=lng,
                                    accuracy=_float(data.get("accuracy"))))
    if u["english"]:
        incident.message_original = " ".join(filter(None, [incident.message_original, u["original"]])).strip()
        incident.message_english = " ".join(filter(None, [incident.message_english, u["english"]])).strip()
        incident.original_language = u["language"] or incident.original_language
    if u["english"] and u["translated"]:
        refresh_guidance_from_message(incident, u["english"])
    db.session.commit()
    for m in new_msgs:
        realtime.emit_chat(incident.id, m.to_dict())
    realtime.emit_incident_update(incident)
    return jsonify({"incident": incident.to_dict(), "created": False}), 200


@bp.get("/sos/current")
@tourist_required
def current(tourist):
    inc = (Incident.query.filter(Incident.tourist_id == tourist.id, Incident.status.in_(Incident.OPEN_STATUSES))
           .order_by(Incident.id.desc()).first())
    return jsonify({"incident": inc.to_dict() if inc else None})


@bp.post("/sos/<int:incident_id>/location")
@tourist_required
def ping(tourist, incident_id):
    inc = Incident.query.get_or_404(incident_id)
    if inc.tourist_id != tourist.id:
        return jsonify({"error": "Forbidden"}), 403
    if not inc.tracking_active or not inc.is_open:
        return jsonify({"error": "Live location sharing is off for this case", "tracking_active": False}), 409
    data = request.get_json(silent=True) or {}
    lat, lng = _coords(data)
    if lat is None:
        return jsonify({"error": "latitude and longitude required"}), 400
    if _coarse(data):
        return jsonify({"ignored": "coarse"}), 202
    p = LocationPing(incident_id=inc.id, latitude=lat, longitude=lng,
                     accuracy=_float(data.get("accuracy")))
    db.session.add(p)
    db.session.commit()
    realtime.emit_location(inc.id, p.to_dict())
    return jsonify({"ping": p.to_dict()}), 201


@bp.post("/sos/<int:incident_id>/tracking")
@tourist_required
def set_tracking(tourist, incident_id):
    """Only the tourist can turn live location off (or on again)."""
    inc = Incident.query.get_or_404(incident_id)
    if inc.tourist_id != tourist.id:
        return jsonify({"error": "Forbidden"}), 403
    if not inc.is_open:
        return jsonify({"error": "This case is closed", "tracking_active": False}), 409
    active = bool((request.get_json(silent=True) or {}).get("active"))
    if active != inc.tracking_active:
        inc.tracking_active = active
        inc.tracking_events = (inc.tracking_events or []) + [
            {"active": active, "at": datetime.utcnow().isoformat() + "Z", "by": "tourist"}]
        msg = _add_chat(inc, "system", "text",
                        "📍 Tourist turned live location ON again." if active
                        else "📍 Tourist turned OFF live location. The map shows the last known position.")
        db.session.commit()
        realtime.emit_chat(inc.id, msg.to_dict())
        realtime.emit_incident_update(inc)
    return jsonify({"tracking_active": inc.tracking_active})


@bp.get("/incidents/<int:incident_id>/pings")
def list_pings(incident_id):
    inc = Incident.query.get_or_404(incident_id)
    if not incident_access(inc):
        return jsonify({"error": "Forbidden"}), 403
    pings = LocationPing.query.filter_by(incident_id=inc.id).order_by(LocationPing.id).all()
    return jsonify({"pings": [p.to_dict() for p in pings], "tracking_active": inc.tracking_active})


def _float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _coarse(data):
    acc = _float((data or {}).get("accuracy"))
    return acc is not None and acc > 1000
