# CLAUDE.md

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimat Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

## Project Goal

Medical research assistant chatbot -- ported from n8n workflow (`Research Handoff agent.json`) into a web app. Three phases: **research gap analysis**, **study methodology design**, **biostatistical analysis**.

`Research Handoff agent.json` is the reference spec. Do not modify it.

## Tech Stack
This project uses uv (not conda/anaconda) for Python package management. Backend is FastAPI/uvicorn. Frontend is Next.js on Vercel. Backend deploys to Render.
- **Backend:** Python, FastAPI, LangGraph (multi-agent orchestration)
- **Frontend:** Next.js (React)
- **Auth:** Supabase Auth (JWT, ES256/HS256) -- `backend/app/auth.py`
- **Billing:** LemonSqueezy (checkout, subscriptions, webhooks) -- `backend/app/api/billing.py`, `backend/app/services/billing.py`
- **LLM:** OpenAI (primary), Google Gemini (fallback)
- **Database:** Supabase PostgreSQL
- **Search:** Tavily API

## Database

- **Supabase PostgreSQL** with asyncpg connection pool (see `backend/app/db.py`)
- All timestamps stored as `TIMESTAMP` (without tz) in **Asia/Bangkok (UTC+7)** local time
- Pool init callback sets `SET timezone = 'Asia/Bangkok'` on every connection -- `server_settings` does NOT work with Supabase PgBouncer
- asyncpg binary protocol ignores session timezone for `TIMESTAMPTZ` columns -- use `TIMESTAMP` (no tz) with `DEFAULT (now() AT TIME ZONE 'Asia/Bangkok')` instead
- Migrations in `backend/migrations/` run in sorted order on startup via `_run_migrations()` in `main.py`
- `CREATE TABLE IF NOT EXISTS` silently skips if table exists with different schema -- verify columns match when debugging
- Tables: `sessions` (PK: session_id TEXT, has `user_id`, `name`, `description`, `ended_at`, `deleted_at`, `updated_at`), `message_logs`, `token_logs`, `session_evaluations`, `subscriptions` (LemonSqueezy), `usage_tracking`, `webhook_events`
- LangGraph auto-creates `checkpoints`, `checkpoint_blobs`, `checkpoint_writes` tables
- `log_message()` and `log_tokens()` are fire-and-forget (asyncio.create_task) -- failures don't break chat

## Commands

CRITICAL: Always use the Makefile or explicit `.venv/bin/` paths. Never run bare
`uvicorn` or `pytest` -- the system PATH may resolve to Anaconda or another Python
that lacks project dependencies.

```bash
# First-time setup
make install

# Start both servers (backend + frontend)
make -j2 dev

# Or individually
make backend          # FastAPI on :8000 via .venv/bin/uvicorn
make frontend         # Next.js on :3000

# Tests
make test             # pytest via .venv/bin/pytest
make lint             # frontend linting
cd frontend && npm run test:e2e   # Playwright E2E tests (32 tests)
cd frontend && npm run test:e2e:ui # Playwright with interactive UI

# Verify environment is healthy
make check-env
```

If you must run commands directly, always prefix with the venv:
```bash
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
cd backend && .venv/bin/pytest
```

## Key Patterns

- All agents return `AgentOutput` (see `backend/app/agents/state.py`) with routing fields
- Supervisor reads `agent_to_route_to` to decide graph transitions
- Secretary agents summarize phase output and set routing
- 20-message sliding window per session (PostgreSQL)
- `forwarded_message` carries context across phase transitions

## Gotchas

- **NEVER run bare `uvicorn` or `pytest`** -- Anaconda shadows the venv. Always use `make backend` / `make test` or explicit `.venv/bin/` paths
- Use `uv` not `pip` for package management
- `timeout` unavailable on macOS -- use `gtimeout` or Python httpx ASGITransport
- Build backend uses `setuptools.build_meta`, not `setuptools.backends._legacy:_Backend`
- `DATABASE_URL` uses `postgresql+asyncpg://` scheme -- strip to `postgresql://` for raw asyncpg (handled by `config.database_dsn`)
- Supabase PgBouncer on port 6543 needs `statement_cache_size=0`
- Frontend pages split into server component (page.tsx exports metadata) + client component (HomeClient.tsx / BenchmarkClient.tsx) for SEO

## Frontend Routes

`/` (landing), `/app` (chat), `/projects` (saved sessions), `/pricing`, `/blog`, `/benchmark`, `/login`, `/auth/callback`, `/account`

## Backend Services

Key services in `backend/app/services/`: `billing.py` (LemonSqueezy checkout/subscriptions), `citation_extractor.py`, `code_executor.py`, `protocol_export.py`, `summary.py`, `file_processor.py`, `memory.py`, `tavily.py`

## Task Tracking

- Plans: `tasks/todo.md`
- Lessons: `tasks/lessons.md` (update after corrections)

## OpenAI Model Reference

Always check `../../Context-hub/openai.md` for correct OpenAI model names before using or changing them. Current models used in this project:
- **Comparison model:** `gpt-5`
- **Simulated user:** `gpt-5-nano`

## Known Production Gaps

- File uploads not persisted to DB (processed in-memory only)
- `createSession()` in `frontend/src/lib/api.ts` is dead code (never called)

## Architecture Details

See `.claude/rules/architecture.md` for full agent definitions, routing contract, state design, and architecture diagram.
