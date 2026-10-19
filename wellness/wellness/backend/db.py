"""
PostgreSQL Database Connection Layer
=========================================
Loads the center/review pool from a real PostgreSQL database (schema.sql)
instead of the JSON file, reconstructing the exact same list-of-dicts
structure matching_engine.py already expects - so no matching-logic
code has to change, only WHERE the data comes from.

Uses PostgreSQL specifically (not MySQL) to match the rest of the team's
stack (itinerary/sos/risk-management components) for the shared tour_ceylon
repository.

HONEST FALLBACK: if PostgreSQL isn't configured/reachable (no DB_PASSWORD
in .env, or connection fails), falls back to the JSON file automatically
and prints which source is actually active - same fallback pattern this
project already uses for AviationStack (falls back to CSV) and the
NLP-review pipeline (falls back to Google star rating). This is not
silent - the startup log always states which data source is live.
"""
import os
import json
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError as PGOperationalError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "tourceylon_app"),
    "password": os.getenv("DB_PASSWORD", ""),
    "dbname": os.getenv("DB_NAME", "tour_ceylon"),
}


def _get_connection():
    if not DB_CONFIG["password"]:
        return None
    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
        return conn
    except PGOperationalError:
        return None


def load_pool_from_postgres():
    conn = _get_connection()
    if conn is None:
        return None, "PostgreSQL not configured or unreachable"

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM centers ORDER BY center_id")
        centers = cursor.fetchall()

        cursor.execute("SELECT center_id, review_text FROM reviews")
        reviews_by_center = {}
        for row in cursor.fetchall():
            reviews_by_center.setdefault(row["center_id"], []).append(row["review_text"])

        pool = []
        for c in centers:
            pool.append({
                "name": c["name"],
                "category": c["category"],
                "conditions_text": c["conditions_text"],
                "dosha_focus": c["dosha_focus"],
                "price_tier": c["price_tier"],
                "phone": c["phone"],
                "lat": float(c["latitude"]) if c["latitude"] is not None else None,
                "lng": float(c["longitude"]) if c["longitude"] is not None else None,
                "district": c["district"],
                "address": c["address"],
                "verified": c["verified_status"],
                "notes": c["notes"],
                "google_rating_real": float(c["google_rating"]) if c["google_rating"] is not None else None,
                "review_count_real": c["google_review_count"],
                "nlp_quality": float(c["nlp_quality_score"]) if c["nlp_quality_score"] is not None else None,
                "quality_source": c["nlp_quality_source"],
                "reviews": reviews_by_center.get(c["center_id"], []),
                "_center_id": c["center_id"],
            })

        cursor.close()
        conn.close()
        return pool, f"PostgreSQL ({DB_CONFIG['dbname']}@{DB_CONFIG['host']})"
    except psycopg2.Error as e:
        return None, f"PostgreSQL query failed: {e}"


def load_pool_from_json():
    with open(os.path.join(DATA_DIR, "full_candidate_pool.json")) as f:
        pool = json.load(f)
    return pool, "JSON file (data/full_candidate_pool.json)"


def load_pool():
    pool, source = load_pool_from_postgres()
    if pool is None:
        print(f"PostgreSQL unavailable ({source}). Falling back to JSON file")
        pool, source = load_pool_from_json()
    print(f"Data source: {source} ({len(pool)} centers)")
    return pool, source


def save_center_update(center_id, updated_fields):
    conn = _get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        field_map = {
            "verified": "verified_status", "notes": "notes", "dosha_focus": "dosha_focus",
            "price_tier": "price_tier", "conditions_text": "conditions_text",
            "name": "name", "category": "category", "district": "district",
        }
        set_clauses, values = [], []
        for k, v in updated_fields.items():
            if k in field_map:
                set_clauses.append(f"{field_map[k]} = %s")
                values.append(v)
        if not set_clauses:
            return False
        values.append(center_id)
        cursor.execute(f"UPDATE centers SET {', '.join(set_clauses)} WHERE center_id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"PostgreSQL update failed: {e}")
        return False
