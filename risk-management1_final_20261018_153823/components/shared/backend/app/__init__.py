"""Tour Ceylon — unified Flask MVC application (Travel + SOS + Wellness)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, verify_jwt_in_request
from flask_sqlalchemy import SQLAlchemy

# __file__ = components/shared/backend/app/__init__.py
_COMPONENTS = Path(__file__).resolve().parents[3]


def _extend_pkg_path(pkg_path, extra: Path) -> None:
    extra_s = str(extra)
    if extra.is_dir() and extra_s not in pkg_path:
        pkg_path.append(extra_s)


# sos_models.py and risk_mount.py live in their component backend folders
_extend_pkg_path(__path__, _COMPONENTS / "sos" / "backend")
_extend_pkg_path(__path__, _COMPONENTS / "risk-management1" / "backend")

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)
load_dotenv(override=False)

db = SQLAlchemy()
jwt = JWTManager()


def _alias_itinerary_model_modules():
    """Itinerary code imports models as components.itinerary.backend.models.*,
    while the unified app also loads the same files as app.models.*.
    Reuse the already-imported modules so SQLAlchemy does not register tables twice.
    """
    names = (
        "accommodation",
        "attraction",
        "budget_split",
        "business_directory",
        "generated_itinerary",
        "saved_reference",
        "tourist_guide",
        "travel_agency",
        "user_trip_input",
    )
    for name in names:
        src = f"app.models.{name}"
        dst = f"components.itinerary.backend.models.{name}"
        if src in sys.modules:
            sys.modules[dst] = sys.modules[src]


def create_app(config_class=None):
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    upload = Path(app.config["UPLOAD_FOLDER"])
    upload.mkdir(parents=True, exist_ok=True)
    for sub in ("photos", "docs", "chat", "chat/image", "chat/voice"):
        (upload / sub).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS") or "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Officer-Language", "X-Site-Language"],
        expose_headers=["Content-Type"],
    )

    # Models (M in MVC) — import submodules without rebinding local `app`
    from app import models as _travel_models  # noqa: F401
    from app import sos_models as _sos_models  # noqa: F401
    from app import sos_models_ext as _sos_models_ext  # noqa: F401
    _alias_itinerary_model_modules()

    # Controllers / routes (C in MVC)
    from app.routes.auth import auth_bp
    from app.routes.attractions import attractions_bp
    from app.routes.trip_input import trip_input_bp
    from app.routes.budget import budget_bp
    from app.routes.accommodation import accommodation_bp
    from app.routes.itinerary import itinerary_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.saved_references import saved_refs_bp
    from app.routes.images import images_bp
    from app.routes.media import media_bp
    from app.routes.tourists import tourists_bp
    from app.routes.hospitals import hospitals_bp
    from app.routes.incidents import incidents_bp
    from app.routes.locations import locations_bp
    from app.routes.notifications import notifications_bp
    from app.routes.chat import chat_bp
    from app.routes.voice import voice_bp
    from app.routes.dispatch import dispatch_bp
    from app.routes.safety import safety_bp
    from app.routes.evidence import evidence_bp
    from app.routes.consent import consent_bp
    from app.routes.geo import geo_bp
    from app.routes.mfa import mfa_bp
    from app.routes.analytics import analytics_bp
    from app.routes.immigration import immigration_bp
    from app.routes.languages import languages_bp
    from app.routes.missing_tourists import missing_tourists_bp
    from app.routes.wellness import wellness_bp

    # Travel
    flask_app = app
    flask_app.register_blueprint(auth_bp, url_prefix="/api/auth")
    flask_app.register_blueprint(attractions_bp, url_prefix="/api")
    flask_app.register_blueprint(trip_input_bp, url_prefix="/api")
    flask_app.register_blueprint(budget_bp, url_prefix="/api/budget")
    flask_app.register_blueprint(accommodation_bp, url_prefix="/api")
    flask_app.register_blueprint(itinerary_bp, url_prefix="/api/itinerary")
    flask_app.register_blueprint(recommendations_bp, url_prefix="/api")
    flask_app.register_blueprint(saved_refs_bp, url_prefix="/api")
    flask_app.register_blueprint(images_bp, url_prefix="/api")
    flask_app.register_blueprint(media_bp, url_prefix="/api")

    # SOS (blueprints already include /api/... prefixes)
    flask_app.register_blueprint(tourists_bp)
    flask_app.register_blueprint(hospitals_bp)
    flask_app.register_blueprint(incidents_bp)
    flask_app.register_blueprint(locations_bp)
    flask_app.register_blueprint(notifications_bp)
    flask_app.register_blueprint(chat_bp)
    flask_app.register_blueprint(voice_bp)
    flask_app.register_blueprint(dispatch_bp)
    flask_app.register_blueprint(safety_bp)
    flask_app.register_blueprint(evidence_bp)
    flask_app.register_blueprint(consent_bp)
    flask_app.register_blueprint(geo_bp)
    flask_app.register_blueprint(mfa_bp)
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(immigration_bp)
    flask_app.register_blueprint(languages_bp)
    flask_app.register_blueprint(missing_tourists_bp)

    # Wellness matcher (Ayurveda / spiritual) — same /api paths as the standalone component
    flask_app.register_blueprint(wellness_bp, url_prefix="/api")

    @flask_app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "app": "tour-ceylon-unified",
            "components": ["travel", "sos", "wellness", "risk"],
        })

    @flask_app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        if filename.startswith("evidence/"):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                from app.sos_models import Incident
                from app.sos_models_ext import Evidence
                item = Evidence.query.filter_by(file_path=filename).first()
                incident = Incident.query.get(item.incident_id) if item else None
                role = claims.get("role")
                allowed = role == "admin" or (
                    role == "tourist" and incident and int(get_jwt_identity()) == incident.tourist_id
                ) or (
                    role in {"officer", "supervisor"}
                    and incident
                    and int(claims.get("station_id", -1)) == incident.station_id
                )
                if not item or not incident or not allowed:
                    return jsonify({"error": "Forbidden"}), 403
            except Exception:
                return jsonify({"error": "Authentication required"}), 401
        return send_from_directory(flask_app.config["UPLOAD_FOLDER"], filename)

    try:
        from app.risk_mount import mount_risk
        mount_risk(flask_app)
    except ModuleNotFoundError:
        flask_app.logger.warning("Risk module not mounted (app.risk_mount missing).")

    from app.services.realtime import init_socketio
    init_socketio(flask_app)

    with flask_app.app_context():
        try:
            # Fresh laptops often have travel tables (login works) but no SOS
            # tables. create_all() only adds missing tables; it never drops data.
            db.create_all()
        except Exception:
            flask_app.logger.exception("Could not create missing database tables")
        try:
            from sqlalchemy import inspect, text

            inspector = inspect(db.engine)
            if "tourists" in inspector.get_table_names():
                cols = {c["name"] for c in inspector.get_columns("tourists")}
                if "profile_completed_at" not in cols:
                    db.session.execute(text("ALTER TABLE tourists ADD COLUMN profile_completed_at TIMESTAMP"))
                    db.session.commit()
            if "budget_split" in inspector.get_table_names():
                cols = {c["name"] for c in inspector.get_columns("budget_split")}
                alters = []
                if "guide" not in cols:
                    alters.append("ALTER TABLE budget_split ADD COLUMN guide NUMERIC DEFAULT 0")
                if "guide_pct" not in cols:
                    alters.append("ALTER TABLE budget_split ADD COLUMN guide_pct NUMERIC DEFAULT 0")
                if "include_guide" not in cols:
                    alters.append("ALTER TABLE budget_split ADD COLUMN include_guide BOOLEAN DEFAULT FALSE")
                for stmt in alters:
                    db.session.execute(text(stmt))
                if alters:
                    db.session.commit()
            from app.sos_schema_migrations import apply_sos_schema_migrations

            apply_sos_schema_migrations(db)
            from app.itinerary_schema_migrations import apply_itinerary_schema_migrations

            apply_itinerary_schema_migrations(db)
            from app.police_login_sync import ensure_police_logins

            ensure_police_logins(db)
        except Exception:
            flask_app.logger.exception("Could not ensure optional schema columns")

    @flask_app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @flask_app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @flask_app.teardown_appcontext
    def _release_db_session(_exc=None):
        db.session.remove()

    return flask_app
