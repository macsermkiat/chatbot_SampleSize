CREATE TABLE IF NOT EXISTS user_profiles (
    user_id       TEXT PRIMARY KEY,
    full_name     TEXT,
    role          TEXT,
    institution   TEXT,
    research_area TEXT,
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok'),
    updated_at    TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
