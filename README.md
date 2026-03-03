# Research Assistant Chatbot

A multi-agent medical research assistant that guides researchers through **gap analysis**, **study methodology design**, and **biostatistical analysis**. Built with LangGraph for orchestration and ported from an n8n workflow into a full-stack web application.

## Features

- **Research Gap Analysis** -- Literature search via Tavily, PICO/PICOTS framing, gap classification, FINER criteria
- **Study Methodology Design** -- Target Trial Emulation, DAG confounding analysis, bias detection, EQUATOR guidelines
- **Biostatistical Analysis** -- Power and sample size calculations, statistical test recommendations, Python/R/STATA code generation
- **File Upload** -- Extract text from PDF, DOCX, and images (OCR)
- **Session Persistence** -- 20-message sliding window stored in PostgreSQL
- **Expertise Levels** -- "Simple" or "Advanced" mode adjusts response depth
- **Streaming Responses** -- Real-time SSE streaming from agents to the chat UI

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, LangGraph |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| LLM | OpenAI (primary), Google Gemini (fallback) |
| Database | Supabase PostgreSQL |
| Search | Tavily API |
| Deployment | Render (backend), Vercel (frontend) |

## Architecture

```
               Next.js Frontend (Chat UI)
                        |
                  FastAPI Backend
                     /api/chat
                        |
                LangGraph StateGraph
                        |
              +---------+---------+
              |                   |
        Orchestrator        File Processor
        (supervisor)        (PDF/DOCX/image)
              |
     +--------+--------+
     |        |        |
  Research  Method-  Biostats
    Gap     ology     Phase
   Phase    Phase       |
                    +---+---+
                    |       |
                 Coding  Diagnostic
                 Agent     Tool
```

All agents return structured output with routing fields. The orchestrator inspects `agent_to_route_to` to decide graph transitions. `forwarded_message` carries context across phase transitions.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- PostgreSQL (or a Supabase project)

### Environment Variables

Create `backend/.env`:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
```

Optional fallback LLMs:

```
GOOGLE_GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

### Run Locally

```bash
# First-time setup
make install

# Start both servers (backend on :8000, frontend on :3000)
make -j2 dev

# Or individually
make backend
make frontend

# Run tests
make test

# Verify environment
make check-env
```

> **Important:** Always use `make` or explicit `.venv/bin/` paths. Never run bare `uvicorn` or `pytest` -- system PATH may resolve to the wrong Python.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | SSE stream of agent responses |
| `/api/upload` | POST | File upload with text extraction |
| `/api/sessions` | POST | Create a new session |
| `/health` | GET | Health check |

### Chat Request

```json
{
  "message": "Calculate sample size for a two-arm RCT",
  "session_id": "uuid",
  "expertise_level": "simple"
}
```

Response is a Server-Sent Events stream with event types: `message`, `phase_change`, `code`, `error`.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes and orchestration
│   │   ├── api/             # FastAPI route handlers
│   │   ├── services/        # LLM, search, file processing, memory
│   │   ├── main.py          # App entrypoint
│   │   └── config.py        # Environment-based settings
│   ├── migrations/          # SQL init scripts
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages and routes
│   │   ├── components/      # React components
│   │   └── lib/             # API client, retry logic
│   ├── package.json
│   └── next.config.js       # API proxy to backend
├── Makefile                  # Development commands
└── render.yaml               # Render deployment config
```

## Deployment

- **Backend** -- Deployed on [Render](https://render.com) via Docker (see `render.yaml`). Includes a `/keep-alive` endpoint on the frontend to mitigate Render cold starts.
- **Frontend** -- Deployed on [Vercel](https://vercel.com) with auto-deploy on push. API requests are proxied to the backend via Next.js rewrites.

## License

This project is for research and educational purposes.
