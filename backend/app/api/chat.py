"""Chat API -- POST /api/chat (SSE streaming)."""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from app.agents.graph import build_graph
from app.agents.state import ResearchState
from app.db import get_pool
from app.models import ChatRequest
from app.services.llm import extract_token_usage
from app.services.memory import get_checkpointer
from app.services.message_logger import log_message, log_tokens

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Build the graph once at module level (stateless; state is per-invocation)
_graph = build_graph()
_compiled_graph = None


def _get_compiled_graph():
    """Return the compiled graph, compiling once on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        checkpointer = get_checkpointer()
        _compiled_graph = _graph.compile(checkpointer=checkpointer)
    return _compiled_graph


async def _ensure_session_exists(session_id: str) -> None:
    """Upsert session row so FK constraints on message_logs/token_logs won't fail."""
    try:
        pool = await get_pool()
        async with pool.acquire(timeout=5) as conn:
            await conn.execute(
                """
                INSERT INTO sessions (session_id, current_phase)
                VALUES ($1, $2)
                ON CONFLICT (session_id) DO NOTHING
                """,
                session_id,
                "orchestrator",
            )
    except Exception:
        _logger.warning("Failed to upsert session %s", session_id, exc_info=True)


async def _stream_graph(
    message: str,
    session_id: str,
    request: Request,
    expertise_level: str = "advanced",
    uploaded_files: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """Run the graph and yield SSE events for each node output."""

    try:
        compiled = _get_compiled_graph()
    except Exception as exc:
        _logger.exception("Failed to compile graph")
        yield {
            "event": "error",
            "data": json.dumps({"error": "Service temporarily unavailable. Please try again later."}),
        }
        return

    # Ensure the session row exists before any FK-dependent writes
    await _ensure_session_exists(session_id)

    config = {"configurable": {"thread_id": session_id}}
    last_emitted_phase = ""

    # Check whether this thread already has state (i.e. a returning session).
    # If so, send only the new user message -- the checkpointer restores
    # prior messages automatically.
    existing = await compiled.aget_state(config)

    if existing.values:
        # Continuing an existing conversation.
        # Only update expertise_level if the caller explicitly sent one.
        input_state: dict = {
            "messages": [HumanMessage(content=message)],
        }
        if expertise_level is not None and expertise_level != existing.values.get("expertise_level"):
            input_state["expertise_level"] = expertise_level
        # Clear or set uploaded_files each turn so stale files don't persist
        input_state["uploaded_files"] = uploaded_files or []
    else:
        # Brand-new session: provide full initial state
        input_state: ResearchState = {
            "messages": [HumanMessage(content=message)],
            "current_phase": "orchestrator",
            "agent_to_route_to": "",
            "forwarded_message": "",
            "needs_clarification": False,
            "need_info": False,
            "session_id": session_id,
            "uploaded_files": uploaded_files or [],
            "code_output": {},
            "search_results": [],
            "expertise_level": expertise_level if expertise_level is not None else "advanced",
            "execution_result": {},
            "stored_python_script": "",
            "has_pending_code": False,
        }

    # Log the user message (fire-and-forget)
    log_message(session_id, "user", message)

    async for event in compiled.astream_events(input_state, config=config, version="v2"):
        kind = event.get("event", "")

        # Emit real-time progress updates from agent nodes
        if kind == "on_custom_event" and event.get("name") == "progress":
            yield {
                "event": "progress",
                "data": json.dumps(event.get("data", {})),
            }
            continue

        # Capture token usage from LLM call completions
        if kind == "on_llm_end":
            data = event.get("data", {})
            llm_output = data.get("output", None)
            if llm_output is not None:
                usage = extract_token_usage(llm_output)
                if usage["total_tokens"] > 0:
                    tags = event.get("tags") or []
                    parent_node = tags[0] if tags else "unknown"
                    log_tokens(
                        session_id,
                        node=parent_node,
                        model=usage["model"],
                        prompt_tokens=usage["prompt_tokens"],
                        completion_tokens=usage["completion_tokens"],
                        total_tokens=usage["total_tokens"],
                    )
                else:
                    _logger.debug(
                        "on_llm_end: zero tokens for session=%s output_type=%s",
                        session_id, type(llm_output).__name__,
                    )

        # Stream node completions as SSE events
        if kind == "on_chain_end" and event.get("name") in _graph.nodes:
            node_name = event["name"]
            output = event.get("data", {}).get("output", {})

            # Extract the AI message content if present
            messages = output.get("messages", [])
            for msg in messages:
                content = getattr(msg, "content", "")
                if content:
                    phase = output.get("current_phase", "")
                    log_message(session_id, "assistant", content, node=node_name, phase=phase)
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "node": node_name,
                            "content": content,
                            "phase": phase,
                        }),
                    }

            # Emit phase change only when the phase actually changes
            new_phase = output.get("current_phase")
            if new_phase and new_phase != last_emitted_phase:
                last_emitted_phase = new_phase
                yield {
                    "event": "phase_change",
                    "data": json.dumps({"phase": new_phase}),
                }

            # Emit code output if present
            code = output.get("code_output")
            if code and code.get("script"):
                yield {
                    "event": "code",
                    "data": json.dumps(code),
                }

    yield {"event": "done", "data": json.dumps({"status": "completed"})}


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Accept a chat message and return an SSE stream of agent responses."""

    session_id = body.session_id or str(uuid.uuid4())

    uploaded_files = [f.model_dump() for f in body.uploaded_files] if body.uploaded_files else None

    async def event_generator():
        try:
            async for event in _stream_graph(
                body.message, session_id, request, body.expertise_level, uploaded_files,
            ):
                yield event
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("SSE stream error for session %s", session_id)
            yield {
                "event": "error",
                "data": json.dumps({"error": "An internal error occurred. Please try again."}),
            }

    return EventSourceResponse(event_generator(), ping=20)
