-- Add user_id column to sessions table for authenticated session ownership.
-- Nullable to support existing anonymous sessions during transition.
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_id TEXT;
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id) WHERE user_id IS NOT NULL;
