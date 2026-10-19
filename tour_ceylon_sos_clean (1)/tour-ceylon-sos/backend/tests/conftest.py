import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Hospital, Officer, Station  # noqa: E402


@pytest.fixture(scope="session")
def _app(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("sos")

    class Cfg:
        TESTING = True
        SECRET_KEY = "test"
        JWT_SECRET_KEY = "test-jwt-secret-that-is-long-enough-for-hs256"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        CORS_ORIGINS = "*"
        WHATSAPP_MODE = "console"
        OPENAI_API_KEY = None

    # One app per test session: Flask-SocketIO's test client only hooks the first server.
    return create_app(Cfg)


@pytest.fixture()
def app(_app):
    application = _app
    application.config.update(WHATSAPP_MODE="console")
    with application.app_context():
        db.drop_all()
        db.create_all()
        ella = Station(name="Ella Police", kind="police", telephone="0572228622", latitude=6.8667, longitude=81.0466)
        colombo = Station(name="Colombo Fort Police", kind="police", telephone="0112421111", latitude=6.935, longitude=79.85)
        tp = Station(name="Ella Tourism Police", kind="tourism_police", telephone="0572228000", latitude=6.875, longitude=81.06)
        db.session.add_all([ella, colombo, tp,
                            Hospital(name="Badulla General Hospital", phone="0552222261", latitude=6.98, longitude=81.05)])
        db.session.flush()
        for uname, st in (("ella-police", ella), ("colombo-fort-police", colombo)):
            o = Officer(username=uname, station_id=st.id)
            o.set_password("Start12345x")
            db.session.add(o)
        db.session.commit()
        yield application
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def tourist(client):
    def make(email="anna@example.com", language="en"):
        r = client.post("/api/auth/tourist/register", json={"name": "Anna", "email": email, "password": "secret123",
                                                            "language": language, "nationality": "German"})
        assert r.status_code == 201, r.json
        return _auth(r.json["token"])
    return make


@pytest.fixture()
def police(client):
    def login(username="ella-police"):
        r = client.post("/api/auth/police/login", json={"username": username, "password": "Start12345x"})
        assert r.status_code == 200
        return _auth(r.json["token"]), r.json["token"]
    return login
