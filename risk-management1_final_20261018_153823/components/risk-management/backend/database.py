"""
database.py — PostgreSQL connection and schema for the Tourism Risk & Context
Intelligence System.

Usage:
    python database.py
This creates the database tables (sites, predictions, feedback) if they
don't already exist. It does NOT seed data — run db_seed.py after this.

Connection settings can be overridden with environment variables:
    DB_HOST     (default: localhost)
    DB_PORT     (default: 5432)
    DB_NAME     (default: tourism_risk_db)
    DB_USER     (default: postgres)
    DB_PASSWORD (default: none — CHANGE this default or set the
                 real env var to match whatever password you actually
                 set when installing PostgreSQL)
"""

import os
import psycopg2
from psycopg2 import sql


DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "tourism_risk_db"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


def get_connection():
    """Open and return a new psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(**DB_CONFIG)


CREATE_SITES_TABLE = """
CREATE TABLE IF NOT EXISTS sites (
    site_id INTEGER PRIMARY KEY,
    site_name VARCHAR(255) NOT NULL,
    district VARCHAR(100),
    province VARCHAR(100),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    category VARCHAR(50),
    annual_visitors_2024 INTEGER,
    capacity_per_day INTEGER,
    entrance_fee_lkr INTEGER,
    is_unesco BOOLEAN DEFAULT FALSE,
    is_eco_friendly BOOLEAN DEFAULT FALSE
);
"""

CREATE_PREDICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES sites(site_id),
    prediction_date DATE NOT NULL,
    crowd_score NUMERIC(5,3),
    risk_level VARCHAR(10),
    is_holiday BOOLEAN,
    is_weekend BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES sites(site_id),
    visit_date DATE,
    observed_crowd_level INTEGER,
    accuracy_rating INTEGER,
    comment TEXT,
    submitted_at TIMESTAMP DEFAULT NOW()
);
"""


def init_db():
    """Create all tables if they don't already exist. Safe to run repeatedly."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_SITES_TABLE)
            cur.execute(CREATE_PREDICTIONS_TABLE)
            cur.execute(CREATE_FEEDBACK_TABLE)
        conn.commit()
        print("Tables created (or already existed): sites, predictions, feedback")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
