-- Separate "deleted" from "ended": ended sessions should still appear
-- in My Projects, but deleted ones should not.
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP DEFAULT NULL;
