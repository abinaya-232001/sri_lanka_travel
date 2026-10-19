"""Mock Department of Immigration and Emigration visa-status API.

Stands in for the real government API during development and demos.
The SOS backend talks to it exactly as it would talk to the real one.

Run:
    pip install flask
    MOCK_IMMIGRATION_API_KEY=demo-immigration-key python app.py      # http://localhost:5055

Then set in the SOS backend environment:
    IMMIGRATION_API_URL=http://localhost:5055
    IMMIGRATION_API_KEY=demo-immigration-key
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, jsonify, request

DATA_FILE = Path(__file__).with_name("travellers.json")
API_KEY = os.environ.get("MOCK_IMMIGRATION_API_KEY", "demo-immigration-key")

app = Flask(__name__)


def _load() -> list[dict]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))["travellers"]


def _save(rows: list[dict]) -> None:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    payload["travellers"] = rows
    DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _day(offset):
    return None if offset is None else (date.today() + timedelta(days=int(offset))).isoformat()


def _norm(value: str | None) -> str:
    return (value or "").strip().upper().replace(" ", "")


def _to_response(row: dict) -> dict:
    valid_until = _day(row.get("valid_until_offset"))
    status = row.get("status") or ("expired" if valid_until and valid_until < date.today().isoformat() else "valid")
    return {
        "reference": row["reference"],
        "passport_number": row["passport_number"],
        "nationality": row["nationality"],
        "full_name": row.get("full_name"),
        "visa_type": row.get("visa_type"),
        "visa_status": status,
        "valid_from": _day(row.get("valid_from_offset")),
        "valid_until": valid_until,
        "entry_date": _day(row.get("entry_offset")),
        "exit_date": _day(row.get("exit_offset")),
    }


@app.before_request
def _check_key():
    if request.path == "/health":
        return None
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Invalid or missing API key"}), 401
    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "mock-immigration-api"})


@app.get("/v1/travellers/visa-status")
def visa_status():
    passport = _norm(request.args.get("passport_number"))
    nationality = _norm(request.args.get("nationality"))
    if not passport:
        return jsonify({"error": "passport_number is required"}), 400
    for row in _load():
        if _norm(row["passport_number"]) == passport and (not nationality or _norm(row["nationality"]) == nationality):
            return jsonify(_to_response(row))
    return jsonify({"error": "No visa record for this passport"}), 404


@app.get("/v1/travellers")
def list_travellers():
    return jsonify({"travellers": [_to_response(r) for r in _load()]})


@app.post("/v1/travellers")
def add_traveller():
    """Demo helper: add or replace a record. Body uses the *_offset fields from travellers.json."""
    body = request.get_json(silent=True) or {}
    for field in ("reference", "passport_number", "nationality"):
        if not body.get(field):
            return jsonify({"error": f"{field} is required"}), 400
    rows = [r for r in _load() if _norm(r["passport_number"]) != _norm(body["passport_number"])]
    rows.append(body)
    _save(rows)
    return jsonify(_to_response(body)), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5055)), debug=True)
