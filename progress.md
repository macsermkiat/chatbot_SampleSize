# Progress Log

## Session: 2026-03-02

### Task: Simple vs Advanced Expertise Level Feature

### Research Phase
- [x] Explored full frontend codebase (page.tsx, api.ts, all components)
- [x] Explored full backend codebase (graph.py, all agent nodes, prompts.py, state.py, models.py, chat.py)
- [x] Analyzed prompt injection pattern across all 7 agent nodes
- [x] Analyzed n8n reference spec for expertise-level-related content
- [x] Reviewed existing test infrastructure (conftest.py, 77 tests)
- [x] Created findings.md with architecture analysis and design decisions
- [x] Created task_plan.md with phased implementation plan

### Key Decisions
1. Style directive prefix approach (not dual prompts) for maintainability
2. Welcome screen card selection UI (not modal or dropdown)
3. `expertise_level` field added to ResearchState and ChatRequest
4. Default "advanced" for backward compatibility
5. Per-agent customization strategy documented

### Implementation Phase
- [x] Phase 1: Backend state + API contract (state.py, models.py, chat.py)
- [x] Phase 2: System prompts -- SIMPLE_STYLE_DIRECTIVE, 7 per-agent addenda (prompts.py)
- [x] Phase 3: Agent node wiring -- prompt_composer.py, updated all 7 nodes
- [x] Phase 4: Frontend UI -- ExpertisePicker.tsx, page.tsx, api.ts
- [x] Phase 5: Tests -- 39 new tests, all passing
- [x] Phase 6: Integration verification -- 116/116 tests pass, TypeScript clean

### Files Created
- `backend/app/agents/prompt_composer.py` -- get_prompt() composition logic
- `frontend/src/components/ExpertisePicker.tsx` -- two-card expertise selector
- `backend/tests/test_expertise_level.py` -- 39 test cases

### Scoring & Fixes (Post-testing)
- [x] Aggressive API testing: 28 test cases across orchestrator, methodology, biostatistics
- [x] Scoring report generated: Overall Grade B- (7.8/10), 25 jargon terms leaked
- [x] Fix: Added BANNED JARGON list (29 terms + replacements) to SIMPLE_STYLE_DIRECTIVE
- [x] Fix: Added no-emoji, varied-opener, response-chunking rules to SIMPLE_STYLE_DIRECTIVE
- [x] Fix: Added formal tone + no-emoji to ADVANCED_STYLE_DIRECTIVE
- [x] Fix: Updated orchestrator to reframe clinical questions instead of routing them
- [x] Fix: Strengthened methodology addendum -- explicit test-name ban, response length cap
- [x] Fix: Strengthened biostatistics addendum -- one-at-a-time questioning, test-name ban
- [x] Fix: Strengthened orchestrator addendum -- jargon ban in routing messages
- [x] Updated 2 tests to check composed prompt instead of addendum alone
- [x] All 116/116 tests pass

### Files Modified
- `backend/app/agents/state.py` -- added ExpertiseLevel type + field
- `backend/app/models.py` -- added expertise_level to ChatRequest
- `backend/app/api/chat.py` -- passes expertise_level to graph state
- `backend/app/agents/prompts.py` -- added style directives, addenda, WELCOME_MESSAGE_SIMPLE
- `backend/app/agents/orchestrator.py` -- uses get_prompt()
- `backend/app/agents/research_gap.py` -- uses get_prompt() in gap_search + gap_summarize
- `backend/app/agents/methodology.py` -- uses get_prompt()
- `backend/app/agents/biostatistics.py` -- uses get_prompt() in biostatistics, diagnostic, coding
- `backend/tests/conftest.py` -- added expertise_level to base_state()
- `frontend/src/app/page.tsx` -- expertise picker flow, header toggle, API plumbing
- `frontend/src/lib/api.ts` -- accepts expertise_level parameter

---

## Session: 2026-03-01 (Previous)

### Agent Workflow Modernization (completed)
- Eliminated secretary layer (11 -> 7 nodes)
- Added smart entry router (skip orchestrator on continuations)
- Added LLM fallback chains (OpenAI -> Gemini)
- Modernized prompts (removed JSON format instructions, n8n artifacts)
- Fixed trim_messages consistency
- 77 tests passing
