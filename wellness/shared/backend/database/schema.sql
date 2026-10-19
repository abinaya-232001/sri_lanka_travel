-- Visily Travel App — PostgreSQL schema
-- Static reference tables are seeded via scripts/seed_data.py
-- Dynamic tables start empty at deploy time

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Auth
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255),
    google_id       VARCHAR(255) UNIQUE,
    auth_provider   VARCHAR(32) NOT NULL DEFAULT 'password',
    name            VARCHAR(255),
    picture         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Static reference tables (read-only at runtime)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accommodation (
    id                          SERIAL PRIMARY KEY,
    "Name"                      TEXT NOT NULL,
    "Category"                  TEXT,
    "Rooms"                     TEXT,
    "Address"                   TEXT,
    "Local Authority"           TEXT,
    normalized_local_authority  TEXT,
    "Web"                       TEXT,
    "Email"                     TEXT,
    "Registration No:"          TEXT,
    "Tel"                       TEXT,
    "Mobile"                    TEXT,
    "Price Range"               TEXT,
    price_min                   NUMERIC,
    price_max                   NUMERIC,
    image                       TEXT
);

CREATE INDEX IF NOT EXISTS idx_accommodation_normalized_la
    ON accommodation (normalized_local_authority);

CREATE TABLE IF NOT EXISTS attractions (
    id                      SERIAL PRIMARY KEY,
    "Attraction Name"       TEXT NOT NULL,
    "Category"              TEXT,
    "Destination"           TEXT,
    normalized_destination  TEXT,
    "Details"               TEXT,
    mood_tag                TEXT,
    image                   TEXT
);

CREATE INDEX IF NOT EXISTS idx_attractions_mood_tag ON attractions (mood_tag);
CREATE INDEX IF NOT EXISTS idx_attractions_normalized_dest ON attractions (normalized_destination);

CREATE TABLE IF NOT EXISTS business_directory (
    id                          SERIAL PRIMARY KEY,
    "Business Name"             TEXT NOT NULL,
    "Address"                   TEXT,
    "Local Authority"           TEXT,
    normalized_local_authority  TEXT,
    "District"                  TEXT,
    "Website"                   TEXT,
    "Email"                     TEXT,
    "Telephone"                 TEXT,
    "Fax"                       TEXT
);

CREATE INDEX IF NOT EXISTS idx_business_directory_normalized_la
    ON business_directory (normalized_local_authority);

CREATE TABLE IF NOT EXISTS travel_agencies (
    id                          SERIAL PRIMARY KEY,
    "Name"                      TEXT NOT NULL,
    "Address"                   TEXT,
    "Local Authority"           TEXT,
    normalized_local_authority  TEXT,
    "Website"                   TEXT,
    "Email"                     TEXT,
    "Registration No."          TEXT,
    "Licence No."               TEXT,
    "Licence Validity"          TEXT,
    "Telephone"                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_travel_agencies_normalized_la
    ON travel_agencies (normalized_local_authority);

CREATE TABLE IF NOT EXISTS tourist_guides (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    guide_type          TEXT,
    languages           TEXT,
    tel                 TEXT,
    address             TEXT,
    registration_no     TEXT,
    email               TEXT,
    validity            TEXT,
    image_url           TEXT
);

CREATE INDEX IF NOT EXISTS idx_tourist_guides_name
    ON tourist_guides (name);
CREATE INDEX IF NOT EXISTS idx_tourist_guides_registration_no
    ON tourist_guides (registration_no);
CREATE INDEX IF NOT EXISTS idx_tourist_guides_guide_type
    ON tourist_guides (guide_type);

-- ---------------------------------------------------------------------------
-- Dynamic user / trip tables
-- ---------------------------------------------------------------------------
CREATE TYPE trip_status AS ENUM ('draft', 'in_progress', 'completed');

CREATE TABLE IF NOT EXISTS user_trip_input (
    trip_id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selected_moods          JSONB NOT NULL DEFAULT '[]'::jsonb,
    days                    INTEGER NOT NULL CHECK (days > 0),
    attractions_by_mood     JSONB NOT NULL DEFAULT '[]'::jsonb,
    attractions_by_days     JSONB NOT NULL DEFAULT '[]'::jsonb,
    finalized_attractions   JSONB NOT NULL DEFAULT '[]'::jsonb,
    budget                  NUMERIC,
    accommodation           TEXT,
    accommodations          JSONB NOT NULL DEFAULT '[]'::jsonb,
    room_type               VARCHAR(16) NOT NULL DEFAULT 'double',
    status                  trip_status NOT NULL DEFAULT 'draft',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_trip_input_user_id ON user_trip_input (user_id);

CREATE TABLE IF NOT EXISTS budget_split (
    trip_id         UUID PRIMARY KEY REFERENCES user_trip_input(trip_id) ON DELETE CASCADE,
    transport       NUMERIC NOT NULL DEFAULT 0,
    food            NUMERIC NOT NULL DEFAULT 0,
    shopping        NUMERIC NOT NULL DEFAULT 0,
    accommodation   NUMERIC NOT NULL DEFAULT 0,
    transport_pct   NUMERIC NOT NULL DEFAULT 25,
    food_pct        NUMERIC NOT NULL DEFAULT 25,
    accommodation_pct NUMERIC NOT NULL DEFAULT 35,
    shopping_pct    NUMERIC NOT NULL DEFAULT 15,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_itinerary (
    id          SERIAL PRIMARY KEY,
    trip_id     UUID NOT NULL REFERENCES user_trip_input(trip_id) ON DELETE CASCADE,
    itinerary   JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_itinerary_trip_id ON generated_itinerary (trip_id);

CREATE TYPE saved_ref_type AS ENUM ('business_directory', 'travel_agency', 'tourist_guide');

CREATE TABLE IF NOT EXISTS saved_references (
    id          SERIAL PRIMARY KEY,
    trip_id     UUID NOT NULL REFERENCES user_trip_input(trip_id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ref_type    saved_ref_type NOT NULL,
    ref_id      INTEGER NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (trip_id, ref_type, ref_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_references_trip_id ON saved_references (trip_id);

-- ---------------------------------------------------------------------------
-- Wellness matcher (Ayurveda & spiritual tourism)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wellness_centers (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    category            VARCHAR(80) NOT NULL,
    conditions_text     TEXT,
    dosha_focus         VARCHAR(50),
    price_tier          VARCHAR(50),
    phone               VARCHAR(50),
    latitude            NUMERIC(9, 6),
    longitude           NUMERIC(9, 6),
    district            VARCHAR(100),
    address             VARCHAR(500),
    verified_status     VARCHAR(255),
    notes               TEXT,
    google_rating       NUMERIC(3, 1),
    google_review_count INTEGER,
    nlp_quality_score   NUMERIC(4, 2),
    nlp_quality_source  VARCHAR(100),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_wellness_centers_name
    ON wellness_centers (name);

CREATE TABLE IF NOT EXISTS wellness_reviews (
    id              SERIAL PRIMARY KEY,
    center_id       INTEGER NOT NULL REFERENCES wellness_centers(id) ON DELETE CASCADE,
    review_text     TEXT NOT NULL,
    is_risk_flagged BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_wellness_reviews_center_id
    ON wellness_reviews (center_id);

CREATE TABLE IF NOT EXISTS wellness_condition_mappings (
    id                      SERIAL PRIMARY KEY,
    condition_name          VARCHAR(255) NOT NULL UNIQUE,
    duration_range          VARCHAR(100),
    duration_source         VARCHAR(500),
    outcome_likelihood_pct  INTEGER,
    outcome_source          VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS wellness_matching_sessions (
    id                          SERIAL PRIMARY KEY,
    tourist_id                  INTEGER,
    user_id                     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    path                        VARCHAR(32) NOT NULL,
    condition_name              VARCHAR(255),
    companion_condition_name    VARCHAR(255),
    predicted_dosha             VARCHAR(20),
    dosha_confidence_pct        NUMERIC(5, 1),
    budget_tier                 VARCHAR(50),
    matched_center_id           INTEGER REFERENCES wellness_centers(id) ON DELETE SET NULL,
    match_pct                   INTEGER,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wellness_sessions_tourist
    ON wellness_matching_sessions (tourist_id);
CREATE INDEX IF NOT EXISTS idx_wellness_sessions_user
    ON wellness_matching_sessions (user_id);
