"""Immigration dashboard + visa monitoring + alert publishing."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "components" / "shared" / "backend"))
sys.path.insert(0, str(ROOT / "components" / "sos" / "backend"))

from datetime import date, timedelta  # noqa: E402

from app import create_app, db  # noqa: E402
from app.sos_models import EmergencyContact, Tourist  # noqa: E402
from app.services.immigration_monitor import is_overstay_suspected, sync_alerts_for_police  # noqa: E402
from app.sos_models_ext import ImmigrationSafetyAlert  # noqa: E402


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-at-least-32-bytes"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(Path(__file__).parent / "uploads-immigration")
    CORS_ORIGINS = ["*"]


def _seed_tourist(*, expired=False):
    tourist = Tourist(
        name="Demo Tourist",
        email="demo@example.com",
        auth_provider="local",
        nationality="UK",
        secure_tourist_id="TSL-TEST-001",
        visa_type="ETA Tourist",
        visa_expiry=date.today() - timedelta(days=3) if expired else date.today() + timedelta(days=10),
        travel_purpose="Tourism",
        trip_start=date.today() - timedelta(days=10),
        trip_end=date.today() + timedelta(days=5),
        document_photo_path="/uploads/demo/passport.jpg",
        last_known_lat=6.9271,
        last_known_lng=79.8612,
        privacy_consent=True,
        location_consent=True,
    )
    tourist.set_sensitive(phone="+447700900001", passport_or_nic="UK1234567")
    ec = EmergencyContact(name="Jane Demo", relationship="Spouse")
    ec.set_sensitive(phone="+447700900002", email="jane@example.com")
    tourist.emergency_contact = ec
    db.session.add(tourist)
    db.session.commit()
    return tourist


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _officer_token(client):
    from flask_jwt_extended import create_access_token

    with client.application.app_context():
        return create_access_token(
            identity="1",
            additional_claims={"role": "officer", "station_id": 1},
        )


def _immigration_token(client):
    from flask_jwt_extended import create_access_token

    with client.application.app_context():
        return create_access_token(
            identity="1",
            additional_claims={"role": "immigration_officer"},
        )


def test_integration_dashboard_returns_minimum_fields(client):
    with client.application.app_context():
        _seed_tourist()
    token = _immigration_token(client)
    response = client.get(
        "/api/immigration/integration",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["integration"]["data_policy"] == "minimum_required_for_safety"
    record = payload["records"][0]
    assert record["secure_tourist_id"] == "TSL-TEST-001"
    # An uploaded photo alone is no longer "verified" — only the immigration API verifies.
    assert record["passport_verification_status"] == "pending"
    assert record["data_source"] == "self_declared"
    assert record["travel_purpose"] == "Tourism"


def test_overstay_detection_and_police_alert_sync(client):
    with client.application.app_context():
        tourist = _seed_tourist(expired=True)
        assert is_overstay_suspected(tourist) is True
        result = sync_alerts_for_police()
        assert result["open_alerts"] >= 1
        alert = ImmigrationSafetyAlert.query.filter_by(
            tourist_id=tourist.id,
            alert_type=ImmigrationSafetyAlert.TYPE_OVERSTAY,
        ).first()
        assert alert is not None

    token = _officer_token(client)
    response = client.get(
        "/api/immigration/police-feed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["summary"]["overstay_suspected"] >= 1
    assert len(payload["alerts"]) >= 1


def test_expired_visa_creates_police_alert_without_location(client):
    with client.application.app_context():
        tourist = _seed_tourist(expired=True)
        tourist.location_consent = False
        tourist.last_known_lat = None
        tourist.last_known_lng = None
        db.session.commit()
        assert is_overstay_suspected(tourist) is False
        sync_alerts_for_police()
        alert = ImmigrationSafetyAlert.query.filter_by(
            tourist_id=tourist.id,
            alert_type=ImmigrationSafetyAlert.TYPE_VISA_EXPIRED,
        ).first()
        assert alert is not None
        assert "expired" in alert.message.lower()


# ---------------------------------------------------------------------------
# Immigration API integration
# ---------------------------------------------------------------------------

from app.services import immigration_api_client  # noqa: E402
from app.services.immigration_api_client import sync_tourist  # noqa: E402


def _api_record(valid_until_days: int, exit_days: int | None = None):
    return {
        "reference": "ETA-TEST-1",
        "passport_number": "UK1234567",
        "nationality": "UK",
        "visa_type": "ETA Tourist (Official)",
        "visa_status": "valid" if valid_until_days >= 0 else "expired",
        "valid_from": (date.today() - timedelta(days=10)).isoformat(),
        "valid_until": (date.today() + timedelta(days=valid_until_days)).isoformat(),
        "entry_date": (date.today() - timedelta(days=9)).isoformat(),
        "exit_date": None if exit_days is None else (date.today() + timedelta(days=exit_days)).isoformat(),
    }


@pytest.fixture()
def api_on(client, monkeypatch):
    client.application.config["IMMIGRATION_API_URL"] = "http://immigration.test"
    client.application.config["IMMIGRATION_API_KEY"] = "k"
    return monkeypatch


def test_api_sync_overrides_self_declared_visa(client, api_on):
    api_on.setattr(immigration_api_client, "fetch_visa_status", lambda p, n: _api_record(3))
    with client.application.app_context():
        tourist = _seed_tourist()  # tourist typed visa_expiry = today + 10
        assert sync_tourist(tourist) == "verified"
        assert tourist.immigration_verified is True
        assert tourist.visa_expiry == date.today() + timedelta(days=3)
        assert tourist.visa_type == "ETA Tourist (Official)"
        assert tourist.trip_start == date.today() - timedelta(days=9)

    token = _immigration_token(client)
    record = client.get("/api/immigration/integration", headers={"Authorization": f"Bearer {token}"}).get_json()["records"][0]
    assert record["passport_verification_status"] == "verified"
    assert record["data_source"] == "immigration_api"
    assert record["immigration_reference"] == "ETA-TEST-1"


def test_api_not_found_keeps_self_declared(client, api_on):
    api_on.setattr(immigration_api_client, "fetch_visa_status", lambda p, n: None)
    with client.application.app_context():
        tourist = _seed_tourist()
        assert sync_tourist(tourist) == "not_found"
        assert tourist.immigration_verified is False
        assert tourist.visa_expiry == date.today() + timedelta(days=10)


def test_official_exit_means_no_overstay_and_no_alerts(client, api_on):
    api_on.setattr(immigration_api_client, "fetch_visa_status", lambda p, n: _api_record(-3, exit_days=-4))
    with client.application.app_context():
        tourist = _seed_tourist(expired=True)
        sync_tourist(tourist)
        assert is_overstay_suspected(tourist) is False
        sync_alerts_for_police()
        assert ImmigrationSafetyAlert.query.filter_by(tourist_id=tourist.id).count() == 0


def test_api_verified_expired_without_exit_is_overstay_even_without_location(client, api_on):
    api_on.setattr(immigration_api_client, "fetch_visa_status", lambda p, n: _api_record(-3))
    with client.application.app_context():
        tourist = _seed_tourist(expired=True)
        tourist.location_consent = False
        tourist.last_known_lat = None
        tourist.last_known_lng = None
        sync_tourist(tourist)
        assert is_overstay_suspected(tourist) is True


def test_api_error_is_recorded_not_raised(client, api_on):
    def boom(p, n):
        raise immigration_api_client.ImmigrationApiError("Immigration API unreachable")

    api_on.setattr(immigration_api_client, "fetch_visa_status", boom)
    with client.application.app_context():
        tourist = _seed_tourist()
        assert sync_tourist(tourist) == "error"
        assert "unreachable" in tourist.immigration_sync_error


def test_sync_route_requires_configuration(client):
    token = _immigration_token(client)
    response = client.post("/api/immigration/sync-from-api", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503


def test_sync_route_syncs_all(client, api_on):
    api_on.setattr(immigration_api_client, "fetch_visa_status", lambda p, n: _api_record(20))
    with client.application.app_context():
        _seed_tourist()
    token = _immigration_token(client)
    response = client.post("/api/immigration/sync-from-api", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["verified"] == 1


def test_police_cannot_trigger_api_sync(client):
    token = _officer_token(client)
    response = client.post("/api/immigration/sync-from-api", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
