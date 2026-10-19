"""Add new columns to existing SOS tables (safe ALTER)."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared", "backend")))

from sqlalchemy import text

from app import create_app, db
from app import sos_models  # noqa: F401
from app import sos_models_ext  # noqa: F401
from app.services.geo_service import seed_fences_from_datasets

ALTERS = [
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_verified BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_source VARCHAR(32) NOT NULL DEFAULT 'self_declared'",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_reference VARCHAR(64)",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_visa_status VARCHAR(32)",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_entry_date DATE",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_exit_date DATE",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_synced_at TIMESTAMP",
    "ALTER TABLE tourists ADD COLUMN IF NOT EXISTS immigration_sync_error VARCHAR(255)",
    "ALTER TABLE officers ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'available'",
    "ALTER TABLE officers ADD COLUMN IF NOT EXISTS last_lat DOUBLE PRECISION",
    "ALTER TABLE officers ADD COLUMN IF NOT EXISTS last_lng DOUBLE PRECISION",
    "ALTER TABLE officers ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP",
    "ALTER TABLE location_pings ADD COLUMN IF NOT EXISTS bearing_deg DOUBLE PRECISION",
    "ALTER TABLE location_pings ADD COLUMN IF NOT EXISTS speed_kmh DOUBLE PRECISION",
    "ALTER TABLE location_pings ADD COLUMN IF NOT EXISTS direction VARCHAR(8)",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS read_at TIMESTAMP",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'sent'",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS duplicate_check_result JSONB",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS duplicate_matched_incident_id INTEGER REFERENCES incidents(id)",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS duplicate_requires_review BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS client_id VARCHAR(128)",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS known_facts JSONB",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS ai_inference JSONB",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_incidents_client_id ON incidents (client_id) WHERE client_id IS NOT NULL",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS voice_transcription TEXT",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS voice_transcription_language VARCHAR(16)",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS voice_stt_provider VARCHAR(64)",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS voice_transcription_confidence DOUBLE PRECISION",
    "CREATE TABLE IF NOT EXISTS safe_journeys (id SERIAL PRIMARY KEY, tourist_id INTEGER NOT NULL REFERENCES tourists(id), origin_name VARCHAR(255) NOT NULL, origin_lat DOUBLE PRECISION NOT NULL, origin_lng DOUBLE PRECISION NOT NULL, destination_name VARCHAR(255) NOT NULL, destination_lat DOUBLE PRECISION NOT NULL, destination_lng DOUBLE PRECISION NOT NULL, expected_duration_minutes INTEGER NOT NULL, started_at TIMESTAMP, expected_arrival_at TIMESTAMP, completed_at TIMESTAMP, cancelled_at TIMESTAMP, escalated_at TIMESTAMP, current_lat DOUBLE PRECISION, current_lng DOUBLE PRECISION, final_lat DOUBLE PRECISION, final_lng DOUBLE PRECISION, cancellation_reason TEXT, status VARCHAR(32) NOT NULL DEFAULT 'not_started', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS safe_journey_events (id SERIAL PRIMARY KEY, journey_id INTEGER NOT NULL REFERENCES safe_journeys(id), event_type VARCHAR(32) NOT NULL, from_status VARCHAR(32), to_status VARCHAR(32), details JSONB, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS missing_tourist_cases (id SERIAL PRIMARY KEY, tourist_id INTEGER NOT NULL REFERENCES tourists(id), reported_by_officer_id INTEGER NOT NULL REFERENCES officers(id), station_id INTEGER NOT NULL REFERENCES stations(id), safe_journey_id INTEGER REFERENCES safe_journeys(id), status VARCHAR(32) NOT NULL DEFAULT 'open', last_known_lat DOUBLE PRECISION, last_known_lng DOUBLE PRECISION, last_interaction_at TIMESTAMP, facts JSONB NOT NULL DEFAULT '{}'::jsonb, ai_inference JSONB, resolved_at TIMESTAMP, resolution_notes TEXT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)",
]


def main():
    app = create_app()
    with app.app_context():
        for sql in ALTERS:
            db.session.execute(text(sql))
        db.session.commit()
        db.create_all()
        count = seed_fences_from_datasets()
        print(f"Migration OK. Geo-fences: {count}")


if __name__ == "__main__":
    main()
