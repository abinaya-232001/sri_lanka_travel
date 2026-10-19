import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import date

from flask import Blueprint, jsonify, request

from app.auth_utils import police_required, token_for_officer, token_for_tourist, tourist_required
from app.extensions import db
from app.models import Officer, Tourist

HANDOFF_SECRET = os.environ.get("HANDOFF_SECRET", "tourceylon-account-handoff")

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _unb64(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@bp.post("/handoff")
def handoff():
    """Accept the signed TourCeylon account and open the matching SOS profile."""
    token = ((request.get_json(silent=True) or {}).get("token") or "").strip()
    try:
        raw, sig = token.split(".", 1)
        body = _unb64(raw)
        expect = hmac.new(HANDOFF_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, sig):
            raise ValueError("signature")
        data = json.loads(body)
        if int(data.get("exp") or 0) < time.time():
            raise ValueError("expired")
        email = str(data.get("email") or "").strip().lower()
        name = str(data.get("name") or "").strip()
        if "@" not in email or len(name) < 2:
            raise ValueError("account")
    except Exception:
        return jsonify({"error": "Sign in with your TourCeylon account again."}), 401
    tourist = Tourist.query.filter_by(email=email).first()
    if not tourist:
        tourist = Tourist(name=name[:120], email=email)
        tourist.set_password(secrets.token_urlsafe(24))
        db.session.add(tourist)
    tourist.name = name[:120]
    tourist.phone = (str(data.get("phone") or "").strip()[:32] or None)
    tourist.nationality = (str(data.get("nationality") or "").strip()[:80] or None)
    tourist.passport = (str(data.get("passport") or "").strip()[:20] or None)
    tourist.language = (str(data.get("language") or "en").strip()[:8] or "en")
    db.session.commit()
    return jsonify({"token": token_for_tourist(tourist), "tourist": tourist.to_dict()})


@bp.post("/tourist/register")
def register():
    return jsonify({"error": "Create your TourCeylon account, then open SOS."}), 410


@bp.post("/tourist/login")
def tourist_login():
    return jsonify({"error": "Sign in with your TourCeylon account, then open SOS."}), 410


@bp.get("/tourist/me")
@tourist_required
def tourist_me(tourist):
    return jsonify({"tourist": tourist.to_dict()})


@bp.patch("/tourist/me")
@tourist_required
def tourist_update(tourist):
    d = request.get_json(silent=True) or {}
    for field, size in (("name", 120), ("phone", 32), ("nationality", 80), ("language", 8), ("visa_type", 80)):
        if field in d:
            tourist.__setattr__(field, (d[field] or "").strip()[:size] or None)
    for field in ("arrival_date", "visa_expiry"):
        if field in d:
            raw = (d.get(field) or "").strip()
            if not raw:
                setattr(tourist, field, None)
            else:
                try:
                    setattr(tourist, field, date.fromisoformat(raw[:10]))
                except ValueError:
                    return jsonify({"error": "Use a real date for the visa."}), 400
    db.session.commit()
    return jsonify({"tourist": tourist.to_dict()})


@bp.post("/police/login")
def police_login():
    d = request.get_json(silent=True) or {}
    o = Officer.query.filter_by(username=(d.get("username") or "").strip().lower()).first()
    if not o or not o.check_password(d.get("password")):
        return jsonify({"error": "Wrong username or password"}), 401
    return jsonify({"token": token_for_officer(o), "station": o.station.to_dict(),
                    "must_change_password": o.must_change_password})


@bp.post("/police/change-password")
@police_required
def change_password(officer):
    d = request.get_json(silent=True) or {}
    if not officer.check_password(d.get("current_password")):
        return jsonify({"error": "Current password is wrong"}), 400
    new = d.get("new_password") or ""
    if len(new) < 10 or new.isalpha() or new.isdigit():
        return jsonify({"error": "Use at least 10 characters with letters and numbers"}), 400
    officer.set_password(new)
    officer.must_change_password = False
    db.session.commit()
    return jsonify({"ok": True})
