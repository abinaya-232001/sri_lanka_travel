-- Add tourist guides reference table + saved_ref_type value (safe for existing DBs)

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON e.enumtypid = t.oid
    WHERE t.typname = 'saved_ref_type'
      AND e.enumlabel = 'tourist_guide'
  ) THEN
    ALTER TYPE saved_ref_type ADD VALUE 'tourist_guide';
  END IF;
END $$;

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
