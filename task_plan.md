# Task Plan: Simple vs Advanced Expertise Level Feature

## Goal
Allow users to choose between "simple" and "advanced" communication modes at the start of a conversation. Simple mode uses plain language (ELI5) for users unfamiliar with research methodology. Advanced mode provides full technical detail (current behavior).

## Scope
- **Backend**: State, API contract, prompts, agent nodes
- **Frontend**: Welcome screen UI, API integration, header toggle
- **Tests**: Unit tests for prompt selection, API tests, component tests

## Constraints
- Preserve SSE streaming contract (no new event types needed)
- Preserve session recovery (checkpointer)
- Preserve routing logic (identical in both modes)
- Default to "advanced" for backward compatibility
- Do not duplicate full prompts -- use style directive overlay

---

## Phase 1: Backend State + API Contract
**Status:** pending
**Files:** `backend/app/agents/state.py`, `backend/app/models.py`, `backend/app/api/chat.py`

### Tasks:
- [ ] 1.1 Add `expertise_level: str` field to `ResearchState` (default "advanced")
- [ ] 1.2 Add `expertise_level: str` field to `ChatRequest` model (optional, default "advanced")
- [ ] 1.3 Update `_stream_graph()` in chat.py to accept and pass `expertise_level` into initial state
- [ ] 1.4 Update `_stream_graph()` to also update `expertise_level` on existing sessions when provided
- [ ] 1.5 Add `ExpertiseLevel = Literal["simple", "advanced"]` type alias

---

## Phase 2: System Prompts (Simple Mode Directives)
**Status:** pending
**Files:** `backend/app/agents/prompts.py`

### Design:
Create a `SIMPLE_STYLE_DIRECTIVE` and `ADVANCED_STYLE_DIRECTIVE` (pass-through) string, plus per-agent simple-mode addenda for agents that need heavier customization.

### Tasks:
- [ ] 2.1 Create `SIMPLE_STYLE_DIRECTIVE` -- global style rules for simple mode:
  - Use plain, everyday language (explain like talking to a smart 12-year-old)
  - Avoid jargon; when technical terms are unavoidable, immediately define them
  - Keep responses short and scannable (bullets, short paragraphs)
  - Use analogies and real-world comparisons
  - Be encouraging and supportive in tone
  - Never assume prior research experience
- [ ] 2.2 Create `ADVANCED_STYLE_DIRECTIVE` -- minimal pass-through (empty or "Use technical terminology appropriate for researchers with epidemiology and biostatistics training.")
- [ ] 2.3 Create `SIMPLE_GAP_SUMMARIZE_ADDENDUM` -- agent-specific overrides:
  - Replace gap taxonomy labels with plain English descriptions
  - Skip GRADE certainty table; just say "strong/moderate/weak evidence"
  - Present research question in plain language, not PICO/PICOTS syntax
  - Limit output to 3-4 bullet points per section
- [ ] 2.4 Create `SIMPLE_METHODOLOGY_ADDENDUM` -- agent-specific overrides:
  - Skip DAG notation, Target Trial Emulation framework, Helsinki references
  - Focus on "what kind of study answers your question" in plain English
  - Use analogies (e.g., "Think of a cohort study like following two groups over time to see what happens")
  - Avoid STROBE/CONSORT/PRISMA labels; just describe what information to report
- [ ] 2.5 Create `SIMPLE_BIOSTATS_ADDENDUM` -- agent-specific overrides:
  - Fully amplify EL12 protocol (already partially exists)
  - Replace "power analysis" with "figuring out how many patients you need"
  - Replace "effect size" with "how big of a difference you expect to find"
  - Replace "alpha/Type I error" with "the chance of a false alarm"
  - Limit mathematical notation; use words instead
- [ ] 2.6 Create `SIMPLE_CODING_ADDENDUM`:
  - Add extensive inline comments explaining each section
  - Use descriptive variable names (not statistical abbreviations)
  - Add a plain-English summary before the code block
- [ ] 2.7 Create `SIMPLE_DIAGNOSTIC_ADDENDUM`:
  - Output in "You should use X because Y" format
  - Skip decision tree structure; just give recommendation with brief rationale
- [ ] 2.8 Create `SIMPLE_ORCHESTRATOR_ADDENDUM`:
  - Use warmer, more guiding tone
  - Explain what each phase does in simple terms when routing
- [ ] 2.9 Update `WELCOME_MESSAGE` to have simple/advanced variants
- [ ] 2.10 Create `get_prompt(base_prompt, expertise_level, agent_name)` helper function that composes the final prompt

---

## Phase 3: Agent Node Wiring
**Status:** pending
**Files:** `backend/app/agents/orchestrator.py`, `backend/app/agents/research_gap.py`, `backend/app/agents/methodology.py`, `backend/app/agents/biostatistics.py`

### Design:
Each node reads `state["expertise_level"]` and calls `get_prompt()` to compose the appropriate system message.

### Tasks:
- [ ] 3.1 Create `backend/app/agents/prompt_composer.py` with `get_prompt()` function
- [ ] 3.2 Update `orchestrator_node` to use `get_prompt(ORCHESTRATOR_PROMPT, state["expertise_level"], "orchestrator")`
- [ ] 3.3 Update `gap_search_node` to use `get_prompt(GAP_SEARCH_PROMPT, state["expertise_level"], "gap_search")`
- [ ] 3.4 Update `gap_summarize_node` to use `get_prompt(GAP_SUMMARIZE_PROMPT, state["expertise_level"], "gap_summarize")`
- [ ] 3.5 Update `methodology_node` to use `get_prompt(METHODOLOGY_PROMPT, state["expertise_level"], "methodology")`
- [ ] 3.6 Update `biostatistics_node` to use `get_prompt(BIOSTATS_PROMPT, state["expertise_level"], "biostatistics")`
- [ ] 3.7 Update `coding_node` to use `get_prompt(CODING_PROMPT, state["expertise_level"], "coding")`
- [ ] 3.8 Update `run_diagnostic` to use `get_prompt(DIAGNOSTIC_PROMPT, state["expertise_level"], "diagnostic")`
- [ ] 3.9 Ensure `entry_router` preserves `expertise_level` in state pass-through

---

## Phase 4: Frontend UI
**Status:** pending
**Files:** `frontend/src/app/page.tsx`, `frontend/src/lib/api.ts`, `frontend/src/components/ExpertisePicker.tsx` (new)

### Design:
Replace the current welcome screen's starter prompts area with an expertise picker first. After selection, show the starter prompts. Add a small toggle in the header for mid-conversation changes.

### Tasks:
- [ ] 4.1 Create `ExpertisePicker.tsx` component:
  - Two cards side by side
  - Left card: "Getting Started" / Simple mode -- icon, title, description ("Plain language explanations, step-by-step guidance. Best for residents, fellows, and students new to research.")
  - Right card: "Advanced" mode -- icon, title, description ("Full technical detail with frameworks and terminology. For researchers familiar with epidemiology and biostatistics.")
  - Framer Motion entry animation matching existing welcome aesthetics
  - onClick callback passes "simple" | "advanced"
- [ ] 4.2 Update `page.tsx` state: add `expertiseLevel` state (null initially, then "simple" | "advanced")
- [ ] 4.3 Update welcome screen flow:
  - Stage 1: Show ExpertisePicker (before any messages)
  - Stage 2: After selection, show starter prompts (existing behavior)
- [ ] 4.4 Update `streamChat()` in api.ts: accept optional `expertise_level` parameter, include in POST body
- [ ] 4.5 Update `sendMessage()` to pass `expertiseLevel` on first message
- [ ] 4.6 Add expertise level indicator/toggle in header (small pill badge next to "Active" indicator)
- [ ] 4.7 Handle mid-conversation expertise change: send updated level with next message
- [ ] 4.8 Style ExpertisePicker to match parchment/scholarly aesthetic

---

## Phase 5: Tests
**Status:** pending
**Files:** `backend/tests/`

### Tasks:
- [ ] 5.1 Test `get_prompt()` function: verify correct composition for simple/advanced modes across all agents
- [ ] 5.2 Test `ChatRequest` model: verify `expertise_level` field validation (only "simple" or "advanced")
- [ ] 5.3 Test `_stream_graph()`: verify `expertise_level` passed into initial state
- [ ] 5.4 Test `_stream_graph()`: verify `expertise_level` preserved on existing sessions
- [ ] 5.5 Test each agent node: verify prompt selection based on `expertise_level` in state
- [ ] 5.6 Test backward compatibility: state without `expertise_level` defaults to "advanced"
- [ ] 5.7 Test orchestrator output: verify simple mode produces warmer, jargon-free response
- [ ] 5.8 Test gap_summarize output: verify simple mode skips GRADE/PICO jargon
- [ ] 5.9 Frontend: verify ExpertisePicker renders both options
- [ ] 5.10 Frontend: verify selection updates state and triggers starter prompts

---

## Phase 6: Integration Verification
**Status:** pending

### Tasks:
- [ ] 6.1 Run full backend test suite (`pytest`)
- [ ] 6.2 Manual test: simple mode end-to-end through all 3 phases
- [ ] 6.3 Manual test: advanced mode end-to-end (regression check)
- [ ] 6.4 Manual test: mid-conversation mode switch
- [ ] 6.5 Manual test: new session defaults (no expertise_level sent = advanced)
- [ ] 6.6 Verify SSE events unchanged (no new event types)
- [ ] 6.7 Run frontend lint (`npm run lint`)

---

## Impact Summary

| Metric | Details |
|--------|---------|
| New files | 2 (prompt_composer.py, ExpertisePicker.tsx) |
| Modified files | ~10 (state.py, models.py, chat.py, prompts.py, 5 agent nodes, page.tsx, api.ts) |
| New prompt text | ~1500 tokens total (directives + addenda) |
| Routing changes | None (routing logic identical in both modes) |
| Breaking changes | None (default "advanced" preserves current behavior) |
| Test additions | ~15-20 new test cases |

---

## Execution Order
Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6
(Sequential: each phase builds on the previous)

## Open Questions
1. Should the welcome message itself change based on expertise level? (Proposed: yes, simpler welcome for simple mode)
2. Should code blocks be hidden entirely in simple mode, or just better-commented? (Proposed: better-commented, not hidden)
