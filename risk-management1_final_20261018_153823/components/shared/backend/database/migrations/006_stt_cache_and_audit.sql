-- Add voice transcription cache and evidence access audit trail
-- Supports multi-provider STT caching and evidence access tracking

-- Create voice_transcripts table for caching STT results
CREATE TABLE IF NOT EXISTS voice_transcripts (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    transcript TEXT NOT NULL,
    language VARCHAR(16) DEFAULT 'en',
    stt_provider VARCHAR(64) NOT NULL,  -- google_cloud, aws_transcribe, openai, etc.
    confidence FLOAT,
    processing_time_ms INTEGER,
    error TEXT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_transcripts_file_path
    ON voice_transcripts (file_path);
CREATE INDEX IF NOT EXISTS idx_voice_transcripts_created_at
    ON voice_transcripts (created_at);
CREATE INDEX IF NOT EXISTS idx_voice_transcripts_success
    ON voice_transcripts (success);

-- Create evidence_access_logs table for audit trail
CREATE TABLE IF NOT EXISTS evidence_access_logs (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER NOT NULL REFERENCES evidence(id),
    actor_role VARCHAR(32) NOT NULL,  -- tourist, officer, admin
    actor_id INTEGER,
    action VARCHAR(32) NOT NULL,  -- upload, view, download, delete, share, legal_hold
    ip_address VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_access_logs_evidence_id
    ON evidence_access_logs (evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_access_logs_actor
    ON evidence_access_logs (actor_role, actor_id);
CREATE INDEX IF NOT EXISTS idx_evidence_access_logs_action
    ON evidence_access_logs (action);
CREATE INDEX IF NOT EXISTS idx_evidence_access_logs_created_at
    ON evidence_access_logs (created_at);

-- Add transcription columns to evidence if not already present
ALTER TABLE evidence
ADD COLUMN IF NOT EXISTS transcription TEXT,
ADD COLUMN IF NOT EXISTS translation TEXT,
ADD COLUMN IF NOT EXISTS original_language VARCHAR(16);
