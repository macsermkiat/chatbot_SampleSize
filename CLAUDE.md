# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Port the n8n multi-agent workflow (`Research Handoff agent.json`) into a fully functional web application. The app is a medical research assistant that guides users through three phases: **research gap analysis**, **study methodology design**, and **biostatistical analysis** (including sample size calculations).

## Tech Stack

- **Backend:** Python, FastAPI, LangGraph (multi-agent orchestration)
- **Frontend:** React (Next.js)
- **LLM Providers:** OpenAI (primary), Google Gemini (fallback)
- **Database:** PostgreSQL (chat memory, session persistence)
- **Storage:** Supabase (structured data), Google Drive (file export)
- **Search:** Tavily API (literature search)

## Reference Workflow

`Research Handoff agent.json` is the source n8n workflow to replicate. Do not modify this file -- it is the reference specification.

## Architecture: LangGraph Multi-Agent with Supervisor

The n8n workflow uses an orchestrator/handoff pattern. Port this to a **LangGraph StateGraph** with a supervisor node.

```
                         Next.js Frontend (Chat UI)
                                |
                          FastAPI Backend
                           /api/chat
                                |
                                v
                    LangGraph StateGraph
                                |
                    +-----------+-----------+
                    |                       |
              Orchestrator            File Processor
              (supervisor)            (PDF/DOCX/image)
                    |
       +------------+------------+
       |            |            |
  ResearchGap   Methodology   Biostatistics
    Phase         Phase         Phase
       |            |            |
  gap_search    methodology   biostats_agent
  gap_summarize  agent        coding_agent
  gap_secretary  meth_secr.   diagnostic_tool
                              biostats_secr.
```

### Agent Definitions (from n8n system prompts)

| Agent | Role | Key Behavior |
|-------|------|-------------|
| **Orchestrator** | Supervisor / triage | Validates scope (gap/methodology/biostats only), routes to specialist, rejects off-topic |
| **ResearchGapSearch** | Literature search | Generates 3-5 search terms, calls Tavily, returns structured results |
| **ResearchGapSummarize** | Evidence appraisal | Gap classification (6 types), PICO/PICOTS formulation, FINER criteria |
| **MethodologyAgent** | Study design | Target Trial Emulation, DAG-based confounding, bias detection, EQUATOR reporting |
| **BiostatisticsAgent** | Power/sample size | Clarification-first approach, "EL12" explanations, calls DiagnosticTool |
| **CodingAgent** | Code generation | Python/R/STATA statistical scripts, code interpreter validation |
| **DiagnosticTool** | Test selection | Statistical test recommendation based on variable types (used as tool, not standalone agent) |
| **Secretary agents** (x3) | Summarize + route | Each phase has a secretary that summarizes output and decides next routing |

### Routing Contract

All agents must return structured output matching this schema:

```python
class AgentOutput(BaseModel):
    direct_response_to_user: str
    agent_to_route_to: str  # "" = stay in current phase
    forwarded_message: str  # context for next agent
    needs_clarification: bool = False
    need_info: bool = False  # biostats-specific
    need_code: bool = False  # coding-specific
```

The supervisor inspects `agent_to_route_to` to decide the next node in the graph. Empty string means continue current conversation; a populated value routes to that phase.

### LangGraph State Design

```python
class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    current_phase: str           # "orchestrator" | "research_gap" | "methodology" | "biostatistics"
    agent_to_route_to: str
    forwarded_message: str
    needs_clarification: bool
    session_id: str
    uploaded_files: list[dict]   # extracted file contents
```

### Memory Strategy

- Per-session message history in PostgreSQL (20-message sliding window, matching n8n config)
- Each agent phase reads from the shared state `messages` list
- `forwarded_message` carries context across phase transitions (not full history replay)

## Planned Directory Structure

```
chatbot_SampleSize/
  Research Handoff agent.json   # reference spec (do not modify)
  CLAUDE.md
  backend/
    app/
      main.py                   # FastAPI app, CORS, lifespan
      config.py                 # env vars, settings
      api/
        chat.py                 # POST /api/chat, WebSocket /api/ws
        files.py                # POST /api/upload (PDF/DOCX/image)
        sessions.py             # session CRUD
      agents/
        state.py                # ResearchState, AgentOutput schema
        graph.py                # LangGraph StateGraph definition
        orchestrator.py         # supervisor/router node
        research_gap.py         # gap_search, gap_summarize, gap_secretary
        methodology.py          # methodology_agent, methodology_secretary
        biostatistics.py        # biostats_agent, coding_agent, diagnostic_tool, biostats_secretary
        prompts.py              # all system prompts (extracted from n8n JSON)
      services/
        llm.py                  # OpenAI + Gemini client setup
        memory.py               # PostgreSQL chat memory (async)
        tavily.py               # Tavily search wrapper
        file_processor.py       # PDF/DOCX/image text extraction
      db.py                     # async PostgreSQL connection
      models.py                 # SQLAlchemy/Pydantic models
    pyproject.toml
    .env.example
  frontend/
    src/
      app/                      # Next.js app router
        page.tsx                # chat interface
        layout.tsx
      components/
        ChatWindow.tsx
        MessageBubble.tsx
        FileUpload.tsx
        PhaseIndicator.tsx      # shows current research phase
      lib/
        api.ts                  # fetch/WebSocket helpers
    package.json
    next.config.js
```

## Commands

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # starts on port 3000

# Tests
cd backend
pytest                        # all tests
pytest tests/test_agents.py   # single file
pytest -k "test_orchestrator" # single test

# Lint
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint
```

## Environment Variables

```
OPENAI_API_KEY=
GOOGLE_GEMINI_API_KEY=
TAVILY_API_KEY=
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/research_chatbot
SUPABASE_URL=
SUPABASE_KEY=
GOOGLE_DRIVE_CREDENTIALS=     # JSON service account or OAuth
```

## Implementation Notes

- Extract all system prompts from the n8n JSON `systemMessage` fields into `prompts.py` -- these are the core domain logic
- The n8n workflow uses OpenAI code interpreter for BiostatisticsAgent/CodingAgent -- replicate via the OpenAI Assistants API `code_interpreter` tool or a sandboxed execution environment
- Tavily search returns `{url, title, content, score}` per result -- the gap_search agent generates 3-5 queries and aggregates results
- File upload pipeline: detect MIME type -> extract text (PyPDF2/python-docx/Pillow+pytesseract) -> attach to state as `uploaded_files`
- The n8n workflow has 22+ webhook chat interaction points -- consolidate these into a single WebSocket connection with message types
- Secretary agents in n8n are separate LLM calls -- in LangGraph these become nodes that summarize the current phase output and set `agent_to_route_to` for the conditional edge
