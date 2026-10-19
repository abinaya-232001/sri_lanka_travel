"""Client for the Department of Immigration and Emigration visa-status API.

Visa details (type, validity, entry/exit dates) are fetched from the immigration
authority by passport number + nationality, instead of trusting what the tourist
types into their profile.

Configuration (Flask config or environment variables):
    IMMIGRATION_API_URL      Base URL, e.g. https://api.immigration.gov.lk  (or http://localhost:5055 for the mock)
    IMMIGRATION_API_KEY      API key issued by the immigration authority (sent as X-API-Key)
    IMMIGRATION_API_TIMEOUT  Seconds, default 8

If IMMIGRATION_API_URL is not set, the integration is disabled and records stay
"self_declared" (the old behaviour).

Expected API contract:
    GET {IMMIGRATION_API_URL}/v1/travellers/visa-status?passport_number=...&nationality=...
    Header: X-API-Key: <key>
    200 -> {
        "reference": "ETA-2026-000123",
        "passport_number": "N1234589",
        "nationality": "India",
        "visa_type": "ETA Tourist (30 days)",
        "visa_status": "valid" | "expired" | "cancelled",
        "valid_from": "2026-10-01",
        "valid_until": "2026-10-30",
        "entry_date": "2026-10-02" | null,
        "exit_date": "2026-10-20" | null
    }
    404 -> traveller / visa not found
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

from flask import current_app

from app import db

SOURCE_API = "immigration_api"
SOURCE_SELF = "self_declared"


class ImmigrationApiError(Exception):
    """Network / auth / server error talking to the immigration API."""


def _cfg(key: str, default=None):
    try:
        value = current_app.config.get(key)
    except RuntimeError:  # outside app context
        value = None
    return value if value not in (None, "") else os.environ.get(key, default)


def api_enabled() -> bool:
    return bool(_cfg("IMMIGRATION_API_URL"))


def api_status() -> dict:
    url = _cfg("IMMIGRATION_API_URL")
    return {
        "enabled": bool(url),
        "provider": "Sri Lanka Department of Immigration and Emigration",
        "base_url": url,
        "has_api_key": bool(_cfg("IMMIGRATION_API_KEY")),
    }


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def fetch_visa_status(passport_number: str, nationality: str | None) -> dict | None:
    """Return the visa record from the immigration API, or None if not found."""
    base = (_cfg("IMMIGRATION_API_URL") or "").rstrip("/")
    if not base:
        raise ImmigrationApiError("IMMIGRATION_API_URL is not configured")

    query = urllib.parse.urlencode({"passport_number": passport_number, "nationality": nationality or ""})
    req = urllib.request.Request(
        f"{base}/v1/travellers/visa-status?{query}",
        headers={"X-API-Key": _cfg("IMMIGRATION_API_KEY", ""), "Accept": "application/json"},
        method="GET",
    )
    timeout = float(_cfg("IMMIGRATION_API_TIMEOUT", 8))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code in (401, 403):
            raise ImmigrationApiError("Immigration API rejected the API key") from exc
        raise ImmigrationApiError(f"Immigration API error {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ImmigrationApiError(f"Immigration API unreachable: {exc}") from exc


def sync_tourist(tourist, *, commit: bool = True) -> str:
    """Pull official visa details for one tourist.

    Returns: "verified" | "not_found" | "no_passport" | "disabled" | "error"
    """
    if not api_enabled():
        return "disabled"

    passport = tourist.get_passport_or_nic()
    if not passport or passport == "pending":
        return "no_passport"

    try:
        record = fetch_visa_status(passport.strip(), tourist.nationality)
    except ImmigrationApiError as exc:
        tourist.immigration_sync_error = str(exc)[:255]
        tourist.immigration_synced_at = datetime.utcnow()
        if commit:
            db.session.commit()
        return "error"

    tourist.immigration_synced_at = datetime.utcnow()
    if record is None:
        tourist.immigration_verified = False
        tourist.immigration_source = SOURCE_SELF
        tourist.immigration_sync_error = "Passport not found in immigration records"
        if commit:
            db.session.commit()
        return "not_found"

    # Official data overrides what the tourist typed in.
    tourist.immigration_verified = True
    tourist.immigration_source = SOURCE_API
    tourist.immigration_sync_error = None
    tourist.immigration_reference = record.get("reference")
    tourist.immigration_visa_status = record.get("visa_status")
    tourist.visa_type = record.get("visa_type") or tourist.visa_type
    tourist.visa_expiry = _parse_date(record.get("valid_until")) or tourist.visa_expiry
    tourist.immigration_entry_date = _parse_date(record.get("entry_date"))
    tourist.immigration_exit_date = _parse_date(record.get("exit_date"))
    if tourist.immigration_entry_date:
        tourist.trip_start = tourist.immigration_entry_date
    if commit:
        db.session.commit()
    return "verified"


def sync_all_tourists() -> dict:
    """Sync every tourist. Used by the immigration dashboard 'Sync from Immigration API' button."""
    from app.sos_models import Tourist

    counts = {"verified": 0, "not_found": 0, "no_passport": 0, "error": 0, "disabled": 0}
    if not api_enabled():
        return {**counts, "enabled": False, "total": 0}

    tourists = Tourist.query.order_by(Tourist.id).all()
    for tourist in tourists:
        counts[sync_tourist(tourist, commit=False)] += 1
    db.session.commit()
    return {**counts, "enabled": True, "total": len(tourists), "synced_at": datetime.utcnow().isoformat() + "Z"}


def is_departed(tourist) -> bool:
    """Official exit recorded by immigration (left Sri Lanka)."""
    exit_date = getattr(tourist, "immigration_exit_date", None)
    return bool(exit_date and exit_date <= date.today())
