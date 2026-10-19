"""Tour Ceylon SOS backend."""

from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.extensions import db, jwt, socketio


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))

    from app import models  # noqa: F401
    from app.routes import auth, chat, family, police, sos
    from app.services import realtime  # noqa: F401  (registers socket handlers)

    for module in (auth, family, sos, chat, police):
        app.register_blueprint(module.bp)

    @app.get("/api/health")
    def health():
        from app.services.classifier import model_available

        return jsonify({"ok": True, "model_loaded": model_available()})

    with app.app_context():
        db.create_all()
        cols = {row[1] for row in db.session.execute(db.text("PRAGMA table_info(tourists)"))}
        added = False
        for name, ddl in (
            ("passport", "VARCHAR(20)"),
            ("visa_type", "VARCHAR(80)"),
            ("arrival_date", "DATE"),
            ("visa_expiry", "DATE"),
        ):
            if name not in cols:
                db.session.execute(db.text(f"ALTER TABLE tourists ADD COLUMN {name} {ddl}"))
                added = True
        if added:
            db.session.commit()
        if not app.config.get("TESTING"):
            from app.services.classifier import warm_up

            warm_up()
    return app
