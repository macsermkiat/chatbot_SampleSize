-- Per-user query usage tracking for billing tier enforcement.
CREATE TABLE IF NOT EXISTS usage_tracking (
    id              SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    period_start    TIMESTAMP NOT NULL,
    period_end      TIMESTAMP NOT NULL,
    query_count     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok'),
    UNIQUE (user_id, period_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_user_period ON usage_tracking (user_id, period_start DESC);
