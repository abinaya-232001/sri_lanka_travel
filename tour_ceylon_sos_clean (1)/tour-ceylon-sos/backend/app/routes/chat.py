"""Chat between the tourist and the assigned police station: text, photos, voice notes."""

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import decode_token

from app.auth_utils import incident_access
from app.extensions import db
from app.models import ChatMessage, Incident
from app.services import realtime
from app.services.incident_guidance import refresh_guidance_from_message
from app.services.media import absolute, save_upload
from app.services.speech import translate_to_english, voice_to_english

bp = Blueprint("chat", __name__, url_prefix="/api")


def _translate_for_tourist(text: str, language: str | None) -> str | None:
    """Police write in English; the tourist also sees it in their own language (best effort)."""
    if not text or not language or language.startswith("en"):
        return None
    try:
        import json
        import urllib.parse
        import urllib.request

        url = ("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=en&tl="
               + urllib.parse.quote(language) + "&q=" + urllib.parse.quote(text))
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        return "".join(p[0] for p in data[0] if p and p[0]).strip() or None
    except Exception:
        return None


@bp.get("/incidents/<int:incident_id>/messages")
def list_messages(incident_id):
    inc = Incident.query.get_or_404(incident_id)
    if not incident_access(inc):
        return jsonify({"error": "Forbidden"}), 403
    q = ChatMessage.query.filter_by(incident_id=inc.id)
    since = request.args.get("since_id", type=int)
    if since:
        q = q.filter(ChatMessage.id > since)
    return jsonify({"messages": [m.to_dict() for m in q.order_by(ChatMessage.id).all()]})


@bp.post("/incidents/<int:incident_id>/messages")
def post_message(incident_id):
    inc = Incident.query.get_or_404(incident_id)
    role = incident_access(inc)
    if not role:
        return jsonify({"error": "Forbidden"}), 403
    if inc.status == "closed":
        return jsonify({"error": "This case is closed"}), 409
    kind = (request.form.get("kind") or "text").lower()
    if kind not in ChatMessage.KINDS:
        return jsonify({"error": "kind must be text, image or voice"}), 400
    body = (request.form.get("body") or "").strip() or None
    msg = ChatMessage(incident_id=inc.id, sender_role=role, kind=kind, body=body)

    if kind in ("image", "voice"):
        rel, err = save_upload(request.files.get("file"), inc.id, kind)
        if err:
            return jsonify({"error": err}), 400
        msg.media_path = rel
    elif not body:
        return jsonify({"error": "Message is empty"}), 400

    language = inc.tourist.language if inc.tourist else None
    english = None
    if role == "tourist":
        if kind == "voice":
            v = voice_to_english(absolute(msg.media_path), request.form.get("voice_transcript"),
                                 request.form.get("language") or language)
            msg.body = msg.body or v.get("original")
            msg.body_english = v.get("english")
            english = v.get("english") or msg.body
        elif body:
            src = "en" if (language or "en").startswith("en") and body.isascii() else "auto"
            en, _, _ = translate_to_english(body, src)
            msg.body_english = en if en and en != body else None
            english = en or body
    elif role == "police" and body:
        msg.body_english = body
        msg.body = _translate_for_tourist(body, language) or body

    db.session.add(msg)
    changed = bool(role == "tourist" and english and refresh_guidance_from_message(inc, english))
    db.session.commit()
    realtime.emit_chat(inc.id, msg.to_dict())
    if changed:
        realtime.emit_incident_update(inc)
    payload = {"message": msg.to_dict()}
    if changed:
        payload["incident"] = inc.to_dict(for_police=(role == "police"))
    return jsonify(payload), 201


@bp.get("/media/<path:rel>")
def media(rel):
    """Photos / voice notes. <img>/<audio> cannot send headers, so the JWT may come as ?token=."""
    token = request.args.get("token") or (request.headers.get("Authorization") or "").replace("Bearer ", "")
    try:
        claims = decode_token(token)
    except Exception:
        return jsonify({"error": "Login required"}), 401
    try:
        incident_id = int(rel.split("/", 1)[0])
    except ValueError:
        return jsonify({"error": "Not found"}), 404
    inc = Incident.query.get_or_404(incident_id)
    allowed = (claims.get("role") == "tourist" and int(claims["sub"]) == inc.tourist_id) or \
              (claims.get("role") == "police" and int(claims.get("station_id", -1)) == inc.station_id)
    if not allowed:
        return jsonify({"error": "Forbidden"}), 403
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], rel)
