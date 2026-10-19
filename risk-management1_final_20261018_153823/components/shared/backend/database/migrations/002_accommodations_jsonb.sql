-- Add per-day / per-destination hotel selections (JSON array)
ALTER TABLE user_trip_input
    ADD COLUMN IF NOT EXISTS accommodations JSONB NOT NULL DEFAULT '[]'::jsonb;
