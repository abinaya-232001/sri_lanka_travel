"""Safe ALTER statements for existing SOS tables (idempotent)."""

from sqlalchemy import inspect, text


STATIC_ALTERS = [
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_incidents_client_id ON incidents (client_id) WHERE client_id IS NOT NULL",
    (
        "CREATE TABLE IF NOT EXISTS safe_journeys ("
        "id SERIAL PRIMARY KEY, tourist_id INTEGER NOT NULL REFERENCES tourists(id), "
        "origin_name VARCHAR(255) NOT NULL, origin_lat DOUBLE PRECISION NOT NULL, "
        "origin_lng DOUBLE PRECISION NOT NULL, destination_name VARCHAR(255) NOT NULL, "
        "destination_lat DOUBLE PRECISION NOT NULL, destination_lng DOUBLE PRECISION NOT NULL, "
        "expected_duration_minutes INTEGER NOT NULL, started_at TIMESTAMP, "
        "expected_arrival_at TIMESTAMP, completed_at TIMESTAMP, cancelled_at TIMESTAMP, "
        "escalated_at TIMESTAMP, current_lat DOUBLE PRECISION, current_lng DOUBLE PRECISION, "
        "final_lat DOUBLE PRECISION, final_lng DOUBLE PRECISION, cancellation_reason TEXT, "
        "status VARCHAR(32) NOT NULL DEFAULT 'not_started', "
        "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    ),
    (
        "CREATE TABLE IF NOT EXISTS safe_journey_events ("
        "id SERIAL PRIMARY KEY, journey_id INTEGER NOT NULL REFERENCES safe_journeys(id), "
        "event_type VARCHAR(32) NOT NULL, from_status VARCHAR(32), to_status VARCHAR(32), "
        "details JSONB, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    ),
    (
        "CREATE TABLE IF NOT EXISTS missing_tourist_cases ("
        "id SERIAL PRIMARY KEY, tourist_id INTEGER NOT NULL REFERENCES tourists(id), "
        "reported_by_officer_id INTEGER NOT NULL REFERENCES officers(id), "
        "station_id INTEGER NOT NULL REFERENCES stations(id), "
        "safe_journey_id INTEGER REFERENCES safe_journeys(id), "
        "status VARCHAR(32) NOT NULL DEFAULT 'open', last_known_lat DOUBLE PRECISION, "
        "last_known_lng DOUBLE PRECISION, last_interaction_at TIMESTAMP, "
        "facts JSONB NOT NULL DEFAULT '{}'::jsonb, ai_inference JSONB, resolved_at TIMESTAMP, "
        "resolution_notes TEXT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    ),
]


def _default_clause(column):
    if column.server_default is not None:
        compiled = str(column.server_default.arg)
        if compiled and not compiled.upper().startswith("("):
            return f" DEFAULT {compiled}"
    if column.default is not None and not column.primary_key:
        arg = getattr(column.default, "arg", None)
        if arg is None:
            return ""
        if isinstance(arg, bool):
            return f" DEFAULT {'TRUE' if arg else 'FALSE'}"
        if isinstance(arg, (int, float)):
            return f" DEFAULT {arg}"
        if isinstance(arg, str):
            return f" DEFAULT '{arg}'"
    return ""


def _sync_model_columns(db):
    from app import sos_models, sos_models_ext

    inspector = inspect(db.engine)
    dialect = db.engine.dialect
    tables = set(inspector.get_table_names())

    for module in (sos_models, sos_models_ext):
        for name in dir(module):
            model = getattr(module, name)
            if not isinstance(model, type) or not hasattr(model, "__tablename__"):
                continue
            table = model.__tablename__
            if table not in tables or not hasattr(model, "__table__"):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for column in model.__table__.columns:
                if column.name in existing:
                    continue
                col_type = column.type.compile(dialect=dialect)
                nullable = "" if column.nullable or column.primary_key else " NOT NULL"
                sql = (
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "
                    f"{column.name} {col_type}{nullable}{_default_clause(column)}"
                )
                db.session.execute(text(sql))


def apply_sos_schema_migrations(db):
    for sql in STATIC_ALTERS:
        db.session.execute(text(sql))
    _sync_model_columns(db)
    db.session.commit()
