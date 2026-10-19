"""Immigration integration + visa monitoring + overstay alert publishing."""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta

from app import db
from app.sos_models import Tourist
from app.sos_models_ext import ImmigrationSafetyAlert
from app.services.immigration_api_client import SOURCE_API, SOURCE_SELF, api_status, is_departed

DATA_POLICY = "minimum_required_for_safety"
INTEGRATION_SOURCE_API = "immigration_department_api"
INTEGRATION_SOURCE_LOCAL = "local_tourist_records"
LEGAL_LOCATION_NOTE = (
    "Location signals use tourist-consented SOS events only — not covert or continuous tracking. "
    "Post-expiry monitoring requires legal authorization, transparency, and defined retention."
)
OVERSTAY_LEGAL_NOTE = (
    "Overstay indicators combine expired visa dates with consented location events and expected departure. "
    "Police follow-up requires separate legal authority."
)

# Approximate Sri Lanka city labels for authorized location events (demo geocoding).
_CITY_ZONES = (
    ("Colombo", 6.9271, 79.8612, 35),
    ("Kandy", 7.2906, 80.6337, 25),
    ("Galle", 6.0535, 80.2210, 25),
    ("Negombo", 7.2088, 79.8358, 20),
    ("Jaffna", 9.6615, 80.0255, 25),
)


def mask_passport(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip()
    if len(s) <= 4:
        return "****"
    return f"{s[:2]}{'*' * min(len(s) - 4, 6)}{s[-2:]}"


def mask_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 4:
        return "****"
    return f"{'*' * max(len(digits) - 4, 4)}{digits[-4:]}"


def _api_verified(tourist: Tourist) -> bool:
    return bool(getattr(tourist, "immigration_verified", False))


def passport_verification_status(tourist: Tourist) -> str:
    """verified = confirmed by the immigration API (an uploaded photo is not enough)."""
    passport = tourist.get_passport_or_nic()
    if not passport or passport == "pending":
        return "not_on_file"
    if _api_verified(tourist):
        return "verified"
    return "pending"


def _still_in_country(tourist: Tourist) -> bool:
    if is_departed(tourist):
        return False
    if _api_verified(tourist):
        return True  # no official exit recorded
    return tourist.trip_end is None or tourist.trip_end >= date.today()


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def authorized_location_label(tourist: Tourist) -> str | None:
    if not tourist.location_consent or tourist.last_known_lat is None or tourist.last_known_lng is None:
        return None
    lat, lng = tourist.last_known_lat, tourist.last_known_lng
    best = None
    best_dist = 9999.0
    for name, clat, clng, radius in _CITY_ZONES:
        dist = _haversine_km(lat, lng, clat, clng)
        if dist <= radius and dist < best_dist:
            best = name
            best_dist = dist
    return best or "Sri Lanka (authorized event)"


def visa_status_parts(tourist: Tourist) -> tuple[str, int | None, str]:
    if not tourist.visa_expiry:
        return "unknown", None, "Unknown"
    remaining = (tourist.visa_expiry - date.today()).days
    if remaining > 0:
        status = "active"
    elif remaining == 0:
        status = "active"
        remaining = 0
    else:
        status = "expired"
    if status == "expired":
        attention = "Attention"
    elif remaining is not None and remaining <= 7:
        attention = "Attention"
    else:
        attention = "Normal"
    return status, remaining, attention


def emergency_contact_payload(tourist: Tourist) -> dict | None:
    ec = tourist.emergency_contact
    if not ec:
        return None
    return {
        "name": ec.name,
        "relationship": ec.relationship,
        "phone_masked": mask_phone(ec.get_phone()),
        "legally_available": True,
    }


def build_integration_record(tourist: Tourist) -> dict:
    visa_status, days_remaining, attention = visa_status_parts(tourist)
    return {
        "tourist_id": tourist.id,
        "secure_tourist_id": tourist.secure_tourist_id or f"TSL-{tourist.id:06d}",
        "name": tourist.name,
        "nationality": tourist.nationality,
        "passport_verification_status": passport_verification_status(tourist),
        "passport_masked": mask_passport(tourist.get_passport_or_nic()),
        "visa_type": tourist.visa_type,
        "visa_status": visa_status,
        "visa_valid_from": tourist.trip_start.isoformat() if tourist.trip_start else None,
        "visa_valid_to": tourist.visa_expiry.isoformat() if tourist.visa_expiry else None,
        "visa_validity_period": _visa_validity_label(tourist),
        "arrival_date": tourist.trip_start.isoformat() if tourist.trip_start else None,
        "expected_departure_date": tourist.trip_end.isoformat() if tourist.trip_end else None,
        "travel_purpose": tourist.travel_purpose,
        "emergency_contact": emergency_contact_payload(tourist),
        "days_remaining": days_remaining,
        "status_label": attention,
        "last_authorized_location_event": authorized_location_label(tourist),
        "location_monitoring_legal_basis": LEGAL_LOCATION_NOTE if tourist.location_consent else None,
        "is_overstay_suspected": is_overstay_suspected(tourist),
        "data_source": SOURCE_API if _api_verified(tourist) else SOURCE_SELF,
        "immigration_verified": _api_verified(tourist),
        "immigration_reference": getattr(tourist, "immigration_reference", None),
        "official_entry_date": _iso(getattr(tourist, "immigration_entry_date", None)),
        "official_exit_date": _iso(getattr(tourist, "immigration_exit_date", None)),
        "immigration_synced_at": _iso(getattr(tourist, "immigration_synced_at", None)),
        "immigration_sync_error": getattr(tourist, "immigration_sync_error", None),
    }


def _iso(value):
    return value.isoformat() if value else None


def build_visa_monitoring_card(tourist: Tourist) -> dict:
    visa_status, days_remaining, attention = visa_status_parts(tourist)
    record = build_integration_record(tourist)
    return {
        "tourist_status_heading": "Tourist Status",
        "secure_tourist_id": record["secure_tourist_id"],
        "name": record["name"],
        "nationality": record["nationality"],
        "visa_status": visa_status.capitalize() if visa_status != "unknown" else "Unknown",
        "visa_status_code": visa_status,
        "arrival_date": record["arrival_date"],
        "visa_expiry": record["visa_valid_to"],
        "days_remaining": days_remaining,
        "last_authorized_location_event": record["last_authorized_location_event"],
        "status_label": attention,
        "visa_type": record["visa_type"],
        "expected_departure_date": record["expected_departure_date"],
        "is_overstay_suspected": is_overstay_suspected(tourist),
        "data_source": record["data_source"],
        "immigration_verified": record["immigration_verified"],
        "official_exit_date": record["official_exit_date"],
        "legal_basis_note": LEGAL_LOCATION_NOTE if tourist.location_consent else None,
    }


def _visa_validity_label(tourist: Tourist) -> str | None:
    if tourist.trip_start and tourist.visa_expiry:
        return f"{tourist.trip_start.isoformat()} → {tourist.visa_expiry.isoformat()}"
    if tourist.visa_expiry:
        return f"Until {tourist.visa_expiry.isoformat()}"
    return None


def is_overstay_suspected(tourist: Tourist) -> bool:
    if not tourist.visa_expiry or tourist.visa_expiry >= date.today():
        return False
    if is_departed(tourist):
        return False
    if _api_verified(tourist):
        # Official record: visa expired and no exit stamp -> overstay.
        return True
    still_in_country = tourist.trip_end is None or tourist.trip_end >= date.today()
    has_authorized_location = bool(
        tourist.location_consent and tourist.last_known_lat is not None and tourist.last_known_lng is not None
    )
    return still_in_country and has_authorized_location


def integration_meta(*, authorized: bool = False):
    status = api_status()
    live = status["enabled"]
    return {
        "provider": status["provider"] if live else "Sri Lanka Department of Immigration and Emigration (not connected)",
        "api_enabled": live,
        "api_base_url": status["base_url"],
        "authorized": authorized,
        "external_provider_verified": authorized and live,
        "data_policy": DATA_POLICY,
        "data_policy_note": (
            "Only minimum data required for tourism safety is shared. "
            "Full immigration records are not duplicated on this platform."
        ),
        "location_monitoring_policy": LEGAL_LOCATION_NOTE,
        "last_sync": datetime.utcnow().isoformat() + "Z",
        "source": INTEGRATION_SOURCE_API if live else INTEGRATION_SOURCE_LOCAL,
    }


def build_summary(records: list[dict], alert_days: int) -> dict:
    threshold = date.today() + timedelta(days=alert_days)
    expiring = [
        r
        for r in records
        if r.get("visa_valid_to") and date.fromisoformat(r["visa_valid_to"]) <= threshold
    ]
    return {
        "total_records": len(records),
        "visa_alerts": len(expiring),
        "verified_passports": sum(1 for r in records if r["passport_verification_status"] == "verified"),
        "pending_verification": sum(1 for r in records if r["passport_verification_status"] == "pending"),
        "expired_visas": sum(1 for r in records if r["visa_status"] == "expired"),
        "overstay_suspected": sum(1 for r in records if r.get("is_overstay_suspected")),
        "api_verified": sum(1 for r in records if r.get("immigration_verified")),
        "self_declared": sum(1 for r in records if not r.get("immigration_verified")),
    }


def _upsert_alert(tourist: Tourist, alert_type: str, severity: str, title: str, message: str, legal_note: str, payload: dict):
    existing = ImmigrationSafetyAlert.query.filter_by(
        tourist_id=tourist.id,
        alert_type=alert_type,
        status=ImmigrationSafetyAlert.STATUS_OPEN,
    ).first()
    payload_json = json.dumps(payload)
    if existing:
        existing.severity = severity
        existing.title = title
        existing.message = message
        existing.legal_basis_note = legal_note
        existing.payload_json = payload_json
        existing.published_to_police_at = datetime.utcnow()
        return existing
    alert = ImmigrationSafetyAlert(
        tourist_id=tourist.id,
        secure_tourist_id=tourist.secure_tourist_id or f"TSL-{tourist.id:06d}",
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        legal_basis_note=legal_note,
        payload_json=payload_json,
    )
    db.session.add(alert)
    return alert


def sync_alerts_for_police(alert_days: int = 30) -> dict:
    tourists = Tourist.query.order_by(Tourist.id).all()
    created_or_updated = 0
    threshold = date.today() + timedelta(days=alert_days)

    for tourist in tourists:
        card = build_visa_monitoring_card(tourist)
        secure_id = card["secure_tourist_id"]

        if is_departed(tourist):
            continue  # official exit recorded: no alerts

        if tourist.visa_expiry and tourist.visa_expiry <= threshold and tourist.visa_expiry >= date.today():
            days = (tourist.visa_expiry - date.today()).days
            severity = ImmigrationSafetyAlert.SEVERITY_ATTENTION if days <= 7 else ImmigrationSafetyAlert.SEVERITY_NORMAL
            _upsert_alert(
                tourist,
                ImmigrationSafetyAlert.TYPE_VISA_EXPIRING,
                severity,
                f"Visa expiring soon — {secure_id}",
                f"{secure_id} visa expires on {tourist.visa_expiry.isoformat()} ({days} days remaining).",
                LEGAL_LOCATION_NOTE,
                card,
            )
            created_or_updated += 1

        if tourist.visa_expiry and tourist.visa_expiry < date.today():
            days_over = (date.today() - tourist.visa_expiry).days
            if _still_in_country(tourist):
                _upsert_alert(
                    tourist,
                    ImmigrationSafetyAlert.TYPE_VISA_EXPIRED,
                    ImmigrationSafetyAlert.SEVERITY_CRITICAL,
                    f"Visa expired — {secure_id}",
                    (
                        f"{secure_id} ({card['name']}, {card['nationality']}) visa expired on "
                        f"{tourist.visa_expiry.isoformat()} ({days_over} days ago) and expected departure "
                        f"has not passed."
                    ),
                    OVERSTAY_LEGAL_NOTE,
                    card,
                )
                created_or_updated += 1

        if is_overstay_suspected(tourist):
            days_over = (date.today() - tourist.visa_expiry).days
            _upsert_alert(
                tourist,
                ImmigrationSafetyAlert.TYPE_OVERSTAY,
                ImmigrationSafetyAlert.SEVERITY_CRITICAL,
                f"Possible overstay — {secure_id}",
                (
                    f"{secure_id} visa expired on {tourist.visa_expiry.isoformat()} "
                    f"({days_over} days ago) but authorized location/consent signals suggest presence in Sri Lanka."
                ),
                OVERSTAY_LEGAL_NOTE,
                card,
            )
            created_or_updated += 1

    db.session.commit()
    open_alerts = ImmigrationSafetyAlert.query.filter_by(status=ImmigrationSafetyAlert.STATUS_OPEN).count()
    return {"synced": created_or_updated, "open_alerts": open_alerts}
