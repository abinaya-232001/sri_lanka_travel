"""Socket.IO: instant SOS alerts, chat, typing and live location.

Rooms: station:<id> (all officers of a station), tourist:<id>, incident:<id>.
Only the incident's own tourist and officers of its assigned station may join
an incident room.
"""

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from app.extensions import socketio

_members: dict[str, dict[int, str]] = {}  # sid -> {incident_id: role}


def _claims():
    token = request.args.get("token") or (request.headers.get("Authorization") or "").replace("Bearer ", "")
    try:
        return decode_token(token) if token else None
    except Exception:
        return None


def incident_role(claims, incident_id):
    from app.models import Incident

    if not claims:
        return None
    try:
        inc = Incident.query.get(int(incident_id))
    except (TypeError, ValueError):
        return None
    if inc is None:
        return None
    if claims.get("role") == "police" and int(claims.get("station_id", -1)) == inc.station_id:
        return "police"
    if claims.get("role") == "tourist" and int(claims.get("sub")) == inc.tourist_id:
        return "tourist"
    return None


@socketio.on("connect")
def on_connect():
    claims = _claims()
    if not claims:
        return False
    if claims.get("role") == "police":
        join_room(f"station:{claims.get('station_id')}")
    elif claims.get("role") == "tourist":
        join_room(f"tourist:{claims.get('sub')}")
    emit("connected", {"role": claims.get("role")})


@socketio.on("disconnect")
def on_disconnect():
    _members.pop(request.sid, None)


@socketio.on("join_incident")
def on_join(data):
    iid = (data or {}).get("incident_id")
    role = incident_role(_claims(), iid)
    if not role:
        emit("join_denied", {"incident_id": iid})
        return
    join_room(f"incident:{int(iid)}")
    _members.setdefault(request.sid, {})[int(iid)] = role
    emit("joined_incident", {"incident_id": int(iid), "role": role})


@socketio.on("leave_incident")
def on_leave(data):
    iid = (data or {}).get("incident_id")
    if iid is not None:
        leave_room(f"incident:{int(iid)}")
        _members.get(request.sid, {}).pop(int(iid), None)


@socketio.on("typing")
def on_typing(data):
    try:
        iid = int((data or {}).get("incident_id"))
    except (TypeError, ValueError):
        return
    role = _members.get(request.sid, {}).get(iid)
    if role:
        emit("typing", {"incident_id": iid, "role": role, "is_typing": bool(data.get("is_typing", True))},
             room=f"incident:{iid}", include_self=False)


# --- server-side events ------------------------------------------------------

def emit_new_sos(incident):
    socketio.emit("sos:new", incident.to_dict(for_police=True), room=f"station:{incident.station_id}")


def emit_incident_update(incident):
    socketio.emit("incident:update", incident.to_dict(for_police=True), room=f"station:{incident.station_id}")
    socketio.emit("incident:update", incident.to_dict(), room=f"tourist:{incident.tourist_id}")


def emit_location(incident_id, ping_dict):
    socketio.emit("location:update", ping_dict, room=f"incident:{incident_id}")


def emit_chat(incident_id, message_dict):
    socketio.emit("chat:message", message_dict, room=f"incident:{incident_id}")
