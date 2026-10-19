from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app import db
from app.sos_models import EmergencyContact, Incident, Tourist
from app.services.immigration_api_client import sync_tourist as sync_from_immigration_api

tourists_bp = Blueprint("tourists", __name__, url_prefix="/api/tourists")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_upload(file_storage, subdir: str) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed(file_storage.filename):
        raise ValueError("Unsupported file type")
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = folder / name
    file_storage.save(path)
    return f"{subdir}/{name}"


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def _tourist_token(tourist: Tourist) -> str:
    return create_access_token(
        identity=str(tourist.id),
        additional_claims={"role": "tourist", "tourist_id": tourist.id},
    )


def _require_tourist() -> Tourist | tuple:
    claims = get_jwt()
    if claims.get("role") != "tourist":
        return None, (jsonify({"error": "Tourist login required"}), 403)
    tourist = Tourist.query.get(int(get_jwt_identity()))
    if not tourist:
        return None, (jsonify({"error": "Tourist not found"}), 404)
    return tourist, None


def _verify_google_id_token(id_token: str) -> dict | None:
    """Verify Google ID token via Google tokeninfo endpoint."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or ""
    if not client_id:
        return None
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(id_token)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    if payload.get("aud") != client_id:
        return None
    if payload.get("email_verified") not in (True, "true", "1"):
        # still allow if email present — some accounts may differ
        if not payload.get("email"):
            return None
    return payload


@tourists_bp.get("/auth/config")
def auth_config():
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or ""
    return jsonify({"google_client_id": client_id, "google_enabled": bool(client_id)})


@tourists_bp.post("/register")
def register():
    """
    Visitor registration with email + password (multipart).
    """
    form = request.form
    required = [
        "name",
        "email",
        "password",
        "phone",
        "nationality",
        "passport_or_nic",
        "emergency_name",
        "emergency_phone",
    ]
    missing = [f for f in required if not (form.get(f) or "").strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = form.get("email").strip().lower()
    password = form.get("password") or ""
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if Tourist.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists. Please log in."}), 409

    try:
        photo_path = _save_upload(request.files.get("photo"), "photos")
        doc_path = _save_upload(request.files.get("document_photo"), "docs")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    tourist = Tourist(
        name=form.get("name").strip(),
        email=email,
        auth_provider="local",
        nationality=form.get("nationality").strip(),
        trip_start=_parse_date(form.get("trip_start")),
        trip_end=_parse_date(form.get("trip_end")),
        hotel_name=(form.get("hotel_name") or "").strip() or None,
        hotel_contact=(form.get("hotel_contact") or "").strip() or None,
        photo_path=photo_path,
        document_photo_path=doc_path,
    )
    tourist.set_password(password)
    tourist.set_sensitive(
        phone=form.get("phone").strip(),
        passport_or_nic=form.get("passport_or_nic").strip(),
    )

    contact = EmergencyContact(
        name=form.get("emergency_name").strip(),
        relationship=(form.get("emergency_relationship") or "").strip() or None,
    )
    contact.set_sensitive(
        phone=form.get("emergency_phone").strip(),
        email=(form.get("emergency_email") or "").strip() or None,
    )
    tourist.emergency_contact = contact

    db.session.add(tourist)
    db.session.commit()

    # Pull official visa details from the immigration API (no-op if not configured).
    sync_from_immigration_api(tourist)

    token = _tourist_token(tourist)
    return (
        jsonify(
            {
                "access_token": token,
                "tourist": tourist.to_dict(reveal_sensitive=True),
                "id": tourist.id,
            }
        ),
        201,
    )


@tourists_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    tourist = Tourist.query.filter_by(email=email).first()
    if not tourist or not tourist.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(
        {
            "access_token": _tourist_token(tourist),
            "tourist": tourist.to_dict(reveal_sensitive=True),
        }
    )


def _verify_travel_user(travel_token: str) -> dict | None:
    """Validate travel JWT and return user dict (in-process, then /auth/me fallback)."""
    from flask_jwt_extended import decode_token

    from app.models.user import User

    # 1) Decode with this app's JWT secret (unified monolith)
    try:
        decoded = decode_token(travel_token)
        role = decoded.get("role")
        if role in ("officer", "tourist"):
            return None
        if role not in (None, "travel_user"):
            return None
        sub = decoded.get("sub")
        if sub is not None:
            user = User.query.get(int(sub))
            if user and user.email:
                return user.to_dict()
    except Exception as exc:
        current_app.logger.warning("bridge-travel JWT decode failed: %s", exc)

    # 2) Fallback: hit /api/auth/me (works if same backend is serving travel auth)
    base = (current_app.config.get("TRAVEL_API_URL") or "http://127.0.0.1:5002/api").rstrip("/")
    url = f"{base}/auth/me"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {travel_token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            user = payload.get("user") if isinstance(payload, dict) else None
            if user and user.get("email"):
                return user
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        current_app.logger.warning("bridge-travel /auth/me fallback failed: %s", exc)

    return None


def _ensure_tourist_for_email(email: str, name: str | None = None) -> Tourist:
    """Find or create a stub visitor profile for a verified travel email."""
    email = (email or "").strip().lower()
    display = (name or "").strip() or (email.split("@")[0] if email else "Visitor")
    tourist = Tourist.query.filter_by(email=email).first()
    if tourist:
        if display and tourist.name in (None, "", "Visitor"):
            tourist.name = display
            db.session.commit()
        return tourist

    tourist = Tourist(
        name=display,
        email=email,
        auth_provider="local",
        nationality="Unknown",
    )
    tourist.set_sensitive(phone="pending", passport_or_nic="pending")
    contact = EmergencyContact(name="Pending", relationship=None)
    contact.set_sensitive(phone="pending", email=None)
    tourist.emergency_contact = contact
    db.session.add(tourist)
    db.session.commit()
    return tourist


@tourists_bp.post("/bridge-travel")
def bridge_travel():
    """
    Exchange a Tour Ceylon access_token for a visitor SOS session.
    Used when the travel header SOS button opens the tourist Home dashboard.
    """
    data = request.get_json(silent=True) or {}
    travel_token = (data.get("travel_token") or data.get("access_token") or "").strip()
    if not travel_token:
        return jsonify({"error": "travel_token is required"}), 400

    try:
        user = _verify_travel_user(travel_token)
        if not user or not user.get("email"):
            return jsonify({
                "error": "Your Tour Ceylon login expired. Click Log out, then Log in again, and retry SOS.",
                "code": "session_expired",
            }), 401

        tourist = _ensure_tourist_for_email(user.get("email"), user.get("name"))
        return jsonify(
            {
                "access_token": _tourist_token(tourist),
                "tourist": tourist.to_dict(reveal_sensitive=True),
                "needs_profile": tourist.get_passport_or_nic() == "pending"
                or tourist.nationality == "Unknown",
            }
        )
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("bridge-travel failed")
        return jsonify({
            "error": "Could not open SOS session. Please try again in a moment.",
            "code": "bridge_failed",
            "detail": str(exc) if current_app.debug else None,
        }), 500


@tourists_bp.post("/link-account")
def link_account():
    """
    Shared-account bridge with Tour Ceylon travel app.
    Creates a stub tourist when missing, or verifies password when present.
    Used so one registration/login works for both dashboards.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip() or (email.split("@")[0] if email else "Visitor")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    tourist = Tourist.query.filter_by(email=email).first()
    created = False

    if tourist:
        if tourist.auth_provider == "google" and not tourist.password_hash:
            tourist.set_password(password)
            tourist.auth_provider = "both"
        elif not tourist.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401
        if name and tourist.name in (None, "", "Visitor"):
            tourist.name = name
    else:
        tourist = Tourist(
            name=name,
            email=email,
            auth_provider="local",
            nationality="Unknown",
        )
        tourist.set_password(password)
        tourist.set_sensitive(phone="pending", passport_or_nic="pending")
        contact = EmergencyContact(name="Pending", relationship=None)
        contact.set_sensitive(phone="pending", email=None)
        tourist.emergency_contact = contact
        db.session.add(tourist)
        created = True

    db.session.commit()
    return jsonify(
        {
            "access_token": _tourist_token(tourist),
            "tourist": tourist.to_dict(reveal_sensitive=True),
            "created": created,
            "needs_profile": tourist.get_passport_or_nic() == "pending"
            or tourist.nationality == "Unknown",
        }
    )


@tourists_bp.post("/google")
def google_login():
    """
    Sign in / register with Google ID token.
    New Google users get a minimal profile and should complete details on Profile.
    """
    data = request.get_json(silent=True) or {}
    id_token = data.get("credential") or data.get("id_token") or ""
    if not id_token:
        return jsonify({"error": "Google credential required"}), 400

    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return jsonify({"error": "Google login is not configured on the server"}), 503

    payload = _verify_google_id_token(id_token)
    if not payload:
        return jsonify({"error": "Invalid Google token"}), 401

    sub = payload.get("sub")
    email = (payload.get("email") or "").strip().lower()
    name = (payload.get("name") or email.split("@")[0] or "Visitor").strip()

    tourist = None
    if sub:
        tourist = Tourist.query.filter_by(google_sub=sub).first()
    if not tourist and email:
        tourist = Tourist.query.filter_by(email=email).first()

    created = False
    if not tourist:
        # Minimal Google registration — user completes passport/emergency on Profile
        tourist = Tourist(
            name=name,
            email=email or None,
            google_sub=sub,
            auth_provider="google",
            nationality="Unknown",
        )
        tourist.set_sensitive(phone="pending", passport_or_nic="pending")
        contact = EmergencyContact(name="Pending", relationship=None)
        contact.set_sensitive(phone="pending", email=None)
        tourist.emergency_contact = contact
        db.session.add(tourist)
        created = True
    else:
        if sub and not tourist.google_sub:
            tourist.google_sub = sub
        if email and not tourist.email:
            tourist.email = email
        if tourist.auth_provider == "local":
            tourist.auth_provider = "both"
        elif tourist.auth_provider != "both":
            tourist.auth_provider = "google"

    db.session.commit()
    return jsonify(
        {
            "access_token": _tourist_token(tourist),
            "tourist": tourist.to_dict(reveal_sensitive=True),
            "created": created,
            "needs_profile": tourist.get_passport_or_nic() == "pending"
            or tourist.nationality == "Unknown",
        }
    )


@tourists_bp.get("/me")
@jwt_required()
def me():
    tourist, err = _require_tourist()
    if err:
        return err
    return jsonify({"tourist": tourist.to_dict(reveal_sensitive=True)})


@tourists_bp.patch("/me")
@jwt_required()
def update_me():
    tourist, err = _require_tourist()
    if err:
        return err

    # multipart or JSON
    form = request.form if request.form else {}
    data = request.get_json(silent=True) or {}

    def val(key):
        return form.get(key) if key in form else data.get(key)

    if val("name"):
        tourist.name = str(val("name")).strip()
    nationality_changed = bool(val("nationality")) and str(val("nationality")).strip() != tourist.nationality
    if val("nationality"):
        tourist.nationality = str(val("nationality")).strip()
    if val("hotel_name") is not None:
        tourist.hotel_name = (str(val("hotel_name")).strip() or None)
    if val("hotel_contact") is not None:
        tourist.hotel_contact = (str(val("hotel_contact")).strip() or None)
    if val("trip_start") is not None:
        tourist.trip_start = _parse_date(val("trip_start") or None)
    if val("trip_end") is not None:
        tourist.trip_end = _parse_date(val("trip_end") or None)
    if val("date_of_birth") is not None:
        tourist.date_of_birth = _parse_date(val("date_of_birth") or None)
    if val("gender") is not None:
        tourist.gender = (str(val("gender")).strip() or None)
    # Visa fields are locked once confirmed by the immigration API.
    if val("visa_type") is not None and not tourist.immigration_verified:
        tourist.visa_type = (str(val("visa_type")).strip() or None)
    if val("visa_expiry") is not None and not tourist.immigration_verified:
        tourist.visa_expiry = _parse_date(val("visa_expiry") or None)
    if val("travel_purpose") is not None:
        tourist.travel_purpose = (str(val("travel_purpose")).strip() or None)
    if val("preferred_language") is not None:
        tourist.preferred_language = (str(val("preferred_language")).strip() or "en")
    if val("medical_info") is not None:
        tourist.medical_info = str(val("medical_info")).strip() or None
    if val("allergies") is not None:
        tourist.allergies = str(val("allergies")).strip() or None
    if val("blood_group") is not None:
        tourist.blood_group = str(val("blood_group")).strip() or None
    if val("special_requirements") is not None:
        tourist.special_requirements = str(val("special_requirements")).strip() or None
    if val("privacy_consent") is not None:
        tourist.privacy_consent = str(val("privacy_consent")).lower() in ("1", "true", "yes")
    if val("location_consent") is not None:
        tourist.location_consent = str(val("location_consent")).lower() in ("1", "true", "yes")

    phone = val("phone")
    passport = val("passport_or_nic")
    passport_changed = bool(passport) and str(passport).strip() != (tourist.get_passport_or_nic() or "")
    if phone or passport:
        tourist.set_sensitive(
            phone=(phone or tourist.get_phone() or "").strip(),
            passport_or_nic=(passport or tourist.get_passport_or_nic() or "").strip(),
        )

    new_password = val("password")
    if new_password:
        if len(str(new_password)) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        tourist.set_password(str(new_password))
        if tourist.auth_provider == "google":
            tourist.auth_provider = "both"

    # Emergency contact
    ec = tourist.emergency_contact
    if not ec:
        ec = EmergencyContact(name="Emergency contact")
        ec.set_sensitive(phone="pending")
        tourist.emergency_contact = ec

    if val("emergency_name"):
        ec.name = str(val("emergency_name")).strip()
    if val("emergency_relationship") is not None:
        ec.relationship = (str(val("emergency_relationship")).strip() or None)
    ec_phone = val("emergency_phone")
    ec_email = val("emergency_email")
    if ec_phone or ec_email is not None:
        ec.set_sensitive(
            phone=(ec_phone or ec.get_phone() or "").strip(),
            email=(str(ec_email).strip() if ec_email is not None else ec.get_email()),
        )

    try:
        if request.files.get("photo"):
            tourist.photo_path = _save_upload(request.files.get("photo"), "photos")
        if request.files.get("document_photo"):
            tourist.document_photo_path = _save_upload(request.files.get("document_photo"), "docs")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if passport_changed or nationality_changed:
        tourist.immigration_verified = False  # old verification no longer applies
        tourist.immigration_source = "self_declared"
    db.session.commit()

    # Not yet verified -> check with the immigration API (no-op if not configured).
    if not tourist.immigration_verified:
        sync_from_immigration_api(tourist)

    return jsonify({"tourist": tourist.to_dict(reveal_sensitive=True)})


@tourists_bp.get("/me/incidents")
@jwt_required()
def my_incidents():
    tourist, err = _require_tourist()
    if err:
        return err

    incidents = (
        Incident.query.filter_by(tourist_id=tourist.id)
        .order_by(Incident.triggered_at.desc())
        .all()
    )
    active = [i for i in incidents if i.status != Incident.STATUS_CLOSED]
    history = [i for i in incidents if i.status == Incident.STATUS_CLOSED]

    # Prefer newest open as "current"
    current = active[0] if active else None
    return jsonify(
        {
            "current": current.to_dict(reveal_tourist=False) if current else None,
            "active": [i.to_dict(reveal_tourist=False) for i in active],
            "history": [i.to_dict(reveal_tourist=False) for i in history],
            "all": [i.to_dict(reveal_tourist=False) for i in incidents],
        }
    )


@tourists_bp.get("/<int:tourist_id>")
def get_tourist(tourist_id: int):
    """Legacy public get — prefer /me with JWT."""
    tourist = Tourist.query.get_or_404(tourist_id)
    return jsonify({"tourist": tourist.to_dict(reveal_sensitive=False)})
