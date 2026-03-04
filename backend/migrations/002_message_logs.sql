-- Human-readable message log for reviewing conversation history
-- in the Supabase dashboard.  LangGraph checkpoints are opaque;
-- this table stores the actual user/assistant text.

CREATE TABLE IF NOT EXISTS message_logs (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    node        TEXT,          -- LangGraph node name (e.g. 'orchestrator', 'gap_summarize')
    phase       TEXT,          -- current_phase at time of message
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_message_logs_session
    ON message_logs (session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_message_logs_role
    ON message_logs (role);
