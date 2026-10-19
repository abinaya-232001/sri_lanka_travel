-- Wellness matcher (Ayurveda & spiritual tourism) — PostgreSQL
-- Safe to run on an existing travel_app database.

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
