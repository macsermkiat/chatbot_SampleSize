CREATE TABLE IF NOT EXISTS session_evaluations (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    rating      SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment     TEXT DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok'),
    UNIQUE (session_id)
);
