-- Sessions table for chat session tracking.
-- All timestamps stored as Asia/Bangkok local time (UTC+7).
-- LangGraph checkpoint tables are auto-created by AsyncPostgresSaver.setup().

CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    created_at    TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok'),
    current_phase TEXT NOT NULL DEFAULT 'orchestrator'
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at DESC);
