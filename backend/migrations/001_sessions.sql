-- Sessions table for chat session tracking.
-- LangGraph checkpoint tables are auto-created by AsyncPostgresSaver.setup().

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    current_phase TEXT NOT NULL DEFAULT 'orchestrator'
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at DESC);
