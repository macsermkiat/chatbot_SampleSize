# Findings: Simple vs Advanced Expertise Level Feature

## Architecture Analysis

### Current Prompt Injection Pattern
All 7 agent nodes follow this identical pattern:
```python
llm = get_chat_model("agent_name").with_structured_output(OutputSchema)
messages = [
    SystemMessage(content=PROMPT_CONSTANT),   # <-- injection point
    *trim_messages(state["messages"]),
    HumanMessage(content=build_input_text(state)),
]
result = await llm.ainvoke(messages)
```

**Key insight**: The `SystemMessage(content=PROMPT_CONSTANT)` is the single point where we inject expertise-level-aware prompts. No other code changes needed per-node beyond selecting the right prompt.

### Prompt File
- `backend/app/agents/prompts.py` -- 7 prompt constants: `ORCHESTRATOR_PROMPT`, `GAP_SEARCH_PROMPT`, `GAP_SUMMARIZE_PROMPT`, `METHODOLOGY_PROMPT`, `BIOSTATS_PROMPT`, `DIAGNOSTIC_PROMPT`, `CODING_PROMPT`, `WELCOME_MESSAGE`

### State Definition
- `backend/app/agents/state.py` -- `ResearchState(TypedDict)` has **no** `expertise_level` field
- State flows through all nodes; adding a field makes it available everywhere
- LangGraph checkpointer persists state per session -- expertise_level survives across turns

### API Contract
- `backend/app/models.py` -- `ChatRequest` has `message` and `session_id` only
- `backend/app/api/chat.py` -- `_stream_graph()` builds initial state with hardcoded defaults
- Frontend sends `{ message, session_id }` via POST /api/chat

### Frontend
- `frontend/src/app/page.tsx` -- single React component, no state management library
- No settings UI exists
- Welcome screen: decorative landing with 3 starter prompt buttons
- `frontend/src/lib/api.ts` -- `streamChat(message, sessionId)` sends 2-field JSON

---

## Design Decisions

### D1: Prompt Strategy -- Style Directive Prefix
Instead of maintaining two full copies of each prompt, prepend a **style directive** that adjusts tone and depth:

```python
def get_prompt(base_prompt: str, expertise_level: str) -> str:
    prefix = SIMPLE_STYLE_DIRECTIVE if expertise_level == "simple" else ADVANCED_STYLE_DIRECTIVE
    return f"{prefix}\n\n{base_prompt}"
```

For agents needing heavier customization (methodology, gap_summarize), provide agent-specific simple-mode addenda appended after the base prompt.

**Rationale**: Single source of truth for domain logic; style is an overlay.

### D2: Per-Agent Simple Mode Behavior

| Agent | Simple Mode Changes |
|-------|-------------------|
| Orchestrator | Warmer tone, simpler routing explanations ("Let me connect you with our statistics helper") |
| Gap Search | No change (internal search terms, user doesn't see) |
| Gap Summarize | Plain English gap types, skip GRADE, use analogies, shorter output, question format instead of PICO syntax |
| Methodology | Skip DAG/TTE/Helsinki jargon, focus on "what kind of study fits", use analogies, avoid STROBE/CONSORT labels |
| Biostatistics | Amplify existing EL12 protocol, "how many patients" not "power analysis", analogies throughout |
| Coding | More inline comments, plain variable names, section explanations |
| Diagnostic | Plain English recommendations, brief "why", no decision tree jargon |

### D3: UI Selection Point
Two clickable cards on the welcome screen:
- "I'm new to research" (simple mode) -- with subtitle explaining the experience
- "I'm experienced with research" (advanced mode)

Once selected: stored in React state, sent with the first API call, persisted in backend state.
Header shows current mode with option to toggle mid-conversation.

### D4: API Transport
- Add optional `expertise_level: Literal["simple", "advanced"]` to `ChatRequest`
- Only meaningful on first message; backend stores in `ResearchState`
- Subsequent messages: backend reads from persisted state
- For mid-conversation changes: frontend sends updated value, backend overwrites

### D5: Backward Compatibility
- Default `expertise_level = "advanced"` everywhere
- Existing sessions without the field behave exactly as today
- No migration needed -- LangGraph state defaults handle missing keys

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Routing breaks in simple mode | HIGH | Keep routing instructions identical in both modes; style directive only changes tone/depth |
| Backward compat (existing sessions) | MEDIUM | Default "advanced" when field missing |
| Prompt length increase | LOW | Style directives are ~150-200 tokens |
| Mid-conversation mode switch | LOW | Allow but new messages use new mode; old messages unchanged |
| LLM ignores style directive | LOW | Place directive at top of system message (highest attention) |
