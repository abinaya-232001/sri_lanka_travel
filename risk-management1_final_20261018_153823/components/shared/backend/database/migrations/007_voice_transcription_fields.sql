-- Add voice transcription fields to chat_messages table
-- Supports STT transcription caching and metadata

ALTER TABLE chat_messages
ADD COLUMN IF NOT EXISTS voice_transcription TEXT,
ADD COLUMN IF NOT EXISTS voice_transcription_language VARCHAR(16),
ADD COLUMN IF NOT EXISTS voice_stt_provider VARCHAR(64),
ADD COLUMN IF NOT EXISTS voice_transcription_confidence FLOAT;

CREATE INDEX IF NOT EXISTS idx_chat_messages_voice_transcription
    ON chat_messages (voice_stt_provider)
    WHERE message_type = 'voice' AND voice_transcription IS NOT NULL;
