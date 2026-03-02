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

- **Backend:** Python, FastAPI, LangGraph (multi-agent orchestration)
- **Frontend:** Next.js (React)
- **LLM:** OpenAI (primary), Google Gemini (fallback)
- **Database:** Supabase PostgreSQL
- **Search:** Tavily API

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

## Task Tracking

- Plans: `tasks/todo.md`
- Lessons: `tasks/lessons.md` (update after corrections)

## Architecture Details

See `.claude/rules/architecture.md` for full agent definitions, routing contract, state design, and architecture diagram.
