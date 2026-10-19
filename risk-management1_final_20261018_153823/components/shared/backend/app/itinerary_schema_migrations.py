"""Safe ALTER statements for itinerary tables (idempotent)."""

from sqlalchemy import inspect, text


ITINERARY_ALTERS = [
    "ALTER TABLE user_trip_input ADD COLUMN IF NOT EXISTS accommodations JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE user_trip_input ADD COLUMN IF NOT EXISTS room_type VARCHAR(16) NOT NULL DEFAULT 'double'",
    "ALTER TABLE budget_split ADD COLUMN IF NOT EXISTS guide NUMERIC DEFAULT 0",
    "ALTER TABLE budget_split ADD COLUMN IF NOT EXISTS guide_pct NUMERIC DEFAULT 0",
    "ALTER TABLE budget_split ADD COLUMN IF NOT EXISTS include_guide BOOLEAN DEFAULT FALSE",
]


def apply_itinerary_schema_migrations(db) -> None:
    """Add missing itinerary columns on older travel_app databases."""
    try:
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
    except Exception:
        return

    for stmt in ITINERARY_ALTERS:
        table = stmt.split()[2] if len(stmt.split()) > 2 else ""
        if table and table not in tables:
            continue
        try:
            db.session.execute(text(stmt))
            db.session.commit()
        except Exception:
            db.session.rollback()
