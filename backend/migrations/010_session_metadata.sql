-- Add metadata columns to sessions for the "Saved Projects" feature.
-- A "project" is a named session with optional description.
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP
    DEFAULT (now() AT TIME ZONE 'Asia/Bangkok');
