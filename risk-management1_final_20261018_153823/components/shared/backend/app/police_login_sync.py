"""Sync police station officers from station_credentials.csv (idempotent)."""

from __future__ import annotations

import csv
from pathlib import Path

from app.sos_models import Officer, Station

_COMPONENTS = Path(__file__).resolve().parents[3]
CREDENTIALS_CSV = _COMPONENTS / "sos" / "backend" / "data" / "sos" / "station_credentials.csv"
_COORD_EPS = 0.002  # ~220 m — enough to match the same desk from Excel/CSV


def _truthy(value) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _station_index() -> tuple[dict[str, Station], list[Station]]:
    by_name: dict[str, Station] = {}
    with_coords: list[Station] = []
    for st in Station.query.all():
        by_name[st.display_name] = st
        if st.latitude is not None and st.longitude is not None:
            with_coords.append(st)
    return by_name, with_coords


def _find_station(
    by_name: dict[str, Station],
    with_coords: list[Station],
    display_name: str,
    lat: float | None,
    lng: float | None,
) -> Station | None:
    if display_name and display_name in by_name:
        return by_name[display_name]
    if lat is None or lng is None:
        return None
    for st in with_coords:
        if abs(st.latitude - lat) <= _COORD_EPS and abs(st.longitude - lng) <= _COORD_EPS:
            if display_name and st.display_name != display_name:
                continue
            return st
    return None


def _ensure_station(
    row: dict,
    lat: float | None,
    lng: float | None,
    by_name: dict[str, Station],
    with_coords: list[Station],
) -> Station:
    from app import db

    display_name = (row.get("display_name") or "").strip()
    st = _find_station(by_name, with_coords, display_name, lat, lng)
    if st:
        st.range_name = (row.get("range") or st.range_name or "Sri Lanka Police").strip()
        st.division = (row.get("division") or st.division or "").strip() or None
        st.desk = (row.get("desk") or st.desk or "Police Station").strip() or None
        st.telephone = (row.get("telephone") or st.telephone or "").strip() or None
        if lat is not None:
            st.latitude = lat
        if lng is not None:
            st.longitude = lng
        st.is_dispatchable = _truthy(row.get("is_dispatchable"))
        return st

    st = Station(
        range_name=(row.get("range") or "Sri Lanka Police").strip(),
        division=(row.get("division") or "").strip() or None,
        desk=(row.get("desk") or "Police Station").strip() or None,
        telephone=(row.get("telephone") or "").strip() or None,
        latitude=lat,
        longitude=lng,
        is_dispatchable=_truthy(row.get("is_dispatchable")),
    )
    db.session.add(st)
    db.session.flush()
    by_name[st.display_name] = st
    if lat is not None and lng is not None:
        with_coords.append(st)
    return st


def sync_police_logins_from_csv(db, csv_path: Path | None = None) -> int:
    path = csv_path or CREDENTIALS_CSV
    if not path.is_file():
        return 0

    by_name, with_coords = _station_index()
    officers_by_username = {o.username: o for o in Officer.query.all()}
    officers_by_badge = {o.badge_number: o for o in officers_by_username.values()}

    updated = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            username = (row.get("username") or "").strip().lower()
            password = (row.get("password") or "").strip()
            if not username or not password:
                continue

            lat = _float_or_none(row.get("latitude"))
            lng = _float_or_none(row.get("longitude"))
            station = _ensure_station(row, lat, lng, by_name, with_coords)

            badge = (row.get("badge_number") or f"SLP-{station.id}").strip()
            email = (row.get("email") or f"{username}@police.lk").strip().lower()
            name = (row.get("officer_name") or f"Duty Officer — {station.display_name}").strip()[:200]

            officer = officers_by_username.get(username) or officers_by_badge.get(badge)
            if not officer:
                officer = Officer(
                    name=name,
                    badge_number=badge,
                    username=username,
                    email=email,
                    station_id=station.id,
                    is_active=True,
                )
                officer.set_password(password)
                db.session.add(officer)
                officers_by_username[username] = officer
                officers_by_badge[badge] = officer
                updated += 1
                continue

            officer.name = name
            officer.badge_number = badge
            officer.username = username
            officer.email = email
            officer.station_id = station.id
            officer.is_active = True
            officer.set_password(password)
            officers_by_username[username] = officer
            officers_by_badge[badge] = officer
            updated += 1

    db.session.commit()
    return updated


def ensure_police_logins(db) -> None:
    """Import CSV logins when the dashboard credential set is incomplete."""
    if not CREDENTIALS_CSV.is_file():
        return
    with CREDENTIALS_CSV.open(newline="", encoding="utf-8") as handle:
        expected = sum(1 for _ in csv.DictReader(handle))
    if expected <= 0:
        return
    if Officer.query.count() >= expected:
        return
    sync_police_logins_from_csv(db)
