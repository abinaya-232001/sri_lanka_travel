from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app import db
from app.models.user import User
from app.sos_models import Officer
from app.sos_models_ext import ImmigrationOfficer

auth_bp = Blueprint("auth", __name__)


def _issue_token(user: User):
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": "travel_user"},
    )
    return {"access_token": token, "user": user.to_dict()}


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Travel user or police officer, depending on JWT role claim."""
    claims = get_jwt()
    identity = int(get_jwt_identity())

    if claims.get("role") == "officer":
        officer = Officer.query.get(identity)
        if not officer:
            return jsonify({"error": "Officer not found"}), 404
        return jsonify({"officer": officer.to_dict(), "station_id": claims.get("station_id")})

    if claims.get("role") == "immigration_officer":
        imm = ImmigrationOfficer.query.get(identity)
        if not imm:
            return jsonify({"error": "Immigration officer not found"}), 404
        return jsonify({"immigration_officer": imm.to_dict()})

    user = User.query.get(identity)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, auth_provider="password")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(_issue_token(user)), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Unified login:
    - Police dashboard: username (+ optional email) → officer JWT
    - Travel / tourist apps: email + password → travel user JWT
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip().lower()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Police officer login when username is provided (dashboard sends username)
    if username:
        if not password:
            return jsonify({"error": "Username and password are required"}), 400

        imm = ImmigrationOfficer.query.filter_by(username=username, is_active=True).first()
        if imm and imm.check_password(password):
            token = create_access_token(
                identity=str(imm.id),
                additional_claims={"role": "immigration_officer"},
            )
            return jsonify({"access_token": token, "immigration_officer": imm.to_dict()})

        officer = Officer.query.filter_by(username=username, is_active=True).first()
        if not officer and email:
            officer = Officer.query.filter_by(email=email, is_active=True).first()
        if not officer or not officer.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = create_access_token(
            identity=str(officer.id),
            additional_claims={"station_id": officer.station_id, "role": "officer"},
        )
        return jsonify({"access_token": token, "officer": officer.to_dict()})

    # Travel user login (email + password)
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if user.auth_provider == "google":
        return jsonify(
            {"error": "This account uses Google Sign-In. Please continue with Google."}
        ), 401

    if not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(_issue_token(user))


@auth_bp.route("/link-account", methods=["POST"])
def link_account():
    """
    Shared-account bridge with Tourist SOS.
    Creates a travel user when missing, or verifies password when present.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip() or None

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user = User.query.filter_by(email=email).first()
    created = False

    if user:
        if user.auth_provider == "google":
            user.set_password(password)
            user.auth_provider = "both"
        elif not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401
        if name and not user.name:
            user.name = name
    else:
        user = User(email=email, auth_provider="password", name=name)
        user.set_password(password)
        db.session.add(user)
        created = True

    db.session.commit()
    payload = _issue_token(user)
    payload["created"] = created
    return jsonify(payload)


@auth_bp.route("/google", methods=["POST"])
def google_login():
    """Verify Google ID token from GIS and return app JWT."""
    data = request.get_json() or {}
    credential = data.get("credential") or data.get("id_token") or ""
    if not credential:
        return jsonify({"error": "Google credential is required"}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or ""
    if not client_id:
        return jsonify(
            {
                "error": "Google Sign-In is not configured. Set GOOGLE_CLIENT_ID in backend/.env",
            }
        ), 503

    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError:
        return jsonify({"error": "Invalid or expired Google token"}), 401

    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return jsonify({"error": "Invalid Google token issuer"}), 401
    if not info.get("email_verified", False):
        return jsonify({"error": "Google email is not verified"}), 401

    email = (info.get("email") or "").strip().lower()
    google_sub = info.get("sub") or ""
    name = (info.get("name") or "").strip() or None
    picture = (info.get("picture") or "").strip() or None

    if not email or not google_sub:
        return jsonify({"error": "Google account did not provide email"}), 400

    user = User.query.filter(
        (User.google_id == google_sub) | (User.email == email)
    ).first()

    if user:
        user.google_id = google_sub
        user.name = name or user.name
        user.picture = picture or user.picture
        if user.auth_provider == "password":
            user.auth_provider = "both"
        elif user.auth_provider != "both":
            user.auth_provider = "google"
    else:
        user = User(
            email=email,
            google_id=google_sub,
            name=name,
            picture=picture,
            auth_provider="google",
        )
        user.set_unusable_password()
        db.session.add(user)

    db.session.commit()
    return jsonify(_issue_token(user))


@auth_bp.route("/google/config", methods=["GET"])
def google_config():
    """Public flag so the login page knows whether to show Google button."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or ""
    return jsonify(
        {
            "enabled": bool(client_id),
            "client_id": client_id or None,
        }
    )
