"""Read visa records from the separate immigration API."""

import json
import urllib.error
import urllib.request
from datetime import date

from flask import current_app


class ImmigrationApiError(Exception):
    pass


def fetch_travellers():
    base = (current_app.config.get("IMMIGRATION_API_URL") or "").rstrip("/")
    if not base:
        raise ImmigrationApiError("Immigration API address is not set.")
    req = urllib.request.Request(
        f"{base}/v1/travellers",
        headers={
            "X-API-Key": current_app.config.get("IMMIGRATION_API_KEY") or "",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ImmigrationApiError(f"Immigration API returned {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ImmigrationApiError("Immigration API is not reachable.") from exc
    return payload.get("travellers") or []


def visa_rows(travellers):
    """Turn API records into desk rows. Expiring means the visa ends within 14 days."""
    today = date.today()
    rows = []
    for row in travellers:
        until = _as_date(row.get("valid_until"))
        left = _as_date(row.get("exit_date"))
        if left and left <= today:
            status, days = "departed", None
        elif until is None:
            status, days = "unknown", None
        else:
            days = (until - today).days
            status = "over" if days < 0 else "expiring" if days <= 14 else "valid"
        rows.append({
            "id": row.get("reference") or row.get("passport_number"),
            "reference": row.get("reference"),
            "name": row.get("full_name") or "Visitor",
            "nationality": row.get("nationality"),
            "passport": row.get("passport_number"),
            "visa_type": row.get("visa_type"),
            "arrival_date": row.get("entry_date"),
            "visa_expiry": row.get("valid_until"),
            "days": days,
            "status": status,
            "source": "immigration_api",
        })
    order = {"expiring": 0, "over": 1, "valid": 2, "departed": 3, "unknown": 4}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["days"] if r["days"] is not None else 999, r["name"]))
    return rows


def _as_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
