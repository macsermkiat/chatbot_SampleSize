-- Raw webhook event storage for reliability (process async, retry on failure).
CREATE TABLE IF NOT EXISTS webhook_events (
    id                  SERIAL PRIMARY KEY,
    event_name          TEXT NOT NULL,
    body                TEXT NOT NULL,
    processed           BOOLEAN NOT NULL DEFAULT false,
    processing_error    TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok')
);
