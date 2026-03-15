# CLAUDE.md

## Workflow Orchestration

### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One tack per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

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
- Tables: `sessions` (PK: session_id TEXT), `message_logs` (FK: session_id), `token_logs` (FK: session_id)
- LangGraph auto-creates `checkpoints`, `checkpoint_blobs`, `checkpoint_writes` tables
- Session IDs are client-generated UUIDs (no server auth) -- `createSession()` in api.ts is dead code
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

## Task Tracking

- Plans: `tasks/todo.md`
- Lessons: `tasks/lessons.md` (update after corrections)

## OpenAI Model Reference

Always check `../../Context-hub/openai.md` for correct OpenAI model names before using or changing them. Current models used in this project:
- **Comparison model:** `gpt-5`
- **Simulated user:** `gpt-5-nano`

## Known Production Gaps

- No authentication / user identity (sessions are anonymous UUIDs)
- File uploads not persisted to DB (processed in-memory only)
- No `updated_at` on sessions table
- `createSession()` in `frontend/src/lib/api.ts` is dead code (never called)

## Architecture Details

See `.claude/rules/architecture.md` for full agent definitions, routing contract, state design, and architecture diagram.
