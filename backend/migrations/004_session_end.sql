-- Add ended_at column to sessions table
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP DEFAULT NULL;
