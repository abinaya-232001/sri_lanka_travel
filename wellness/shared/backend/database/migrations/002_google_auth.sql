-- Google Sign-In support on users table (safe for existing DBs)

ALTER TABLE users
    ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(32) NOT NULL DEFAULT 'password';

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS name VARCHAR(255);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS picture TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id
    ON users (google_id)
    WHERE google_id IS NOT NULL;
