-- Room type preference for accommodation pricing (single / double / family)
ALTER TABLE user_trip_input
    ADD COLUMN IF NOT EXISTS room_type VARCHAR(16) NOT NULL DEFAULT 'double';
