-- Cache generated summary text so exports don't re-call the LLM every time.
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS summary_cache TEXT;
