-- LemonSqueezy subscription tracking.
CREATE TABLE IF NOT EXISTS subscriptions (
    id                  SERIAL PRIMARY KEY,
    user_id             TEXT,
    ls_subscription_id  TEXT UNIQUE NOT NULL,
    ls_customer_id      TEXT,
    variant_id          TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'active',
    email               TEXT,
    is_paused           BOOLEAN NOT NULL DEFAULT false,
    renews_at           TIMESTAMP,
    ends_at             TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok'),
    updated_at          TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_ls_id ON subscriptions (ls_subscription_id);
