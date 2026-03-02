"""Chat API -- POST /api/chat (SSE streaming)."""

from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from app.agents.graph import build_graph
from app.agents.state import ResearchState
from app.models import ChatRequest
from app.services.memory import get_checkpointer

router = APIRouter(prefix="/api", tags=["chat"])

# Build the graph once at module level (stateless; state is per-invocation)
_graph = build_graph()


async def _stream_graph(
    message: str,
    session_id: str,
    request: Request,
    expertise_level: str = "advanced",
) -> AsyncGenerator[dict, None]:
    """Run the graph and yield SSE events for each node output."""

    checkpointer = get_checkpointer()
    compiled = _graph.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": session_id}}

    # Check whether this thread already has state (i.e. a returning session).
    # If so, send only the new user message -- the checkpointer restores
    # prior messages automatically.
    existing = await compiled.aget_state(config)

    if existing.values:
        # Continuing an existing conversation.
        # If the caller sent a new expertise_level, update it.
        input_state: dict = {
            "messages": [HumanMessage(content=message)],
        }
        if expertise_level and expertise_level != existing.values.get("expertise_level"):
            input_state["expertise_level"] = expertise_level
    else:
        # Brand-new session: provide full initial state
        input_state: ResearchState = {
            "messages": [HumanMessage(content=message)],
            "current_phase": "orchestrator",
            "agent_to_route_to": "",
            "forwarded_message": "",
            "needs_clarification": False,
            "need_info": False,
            "need_code": False,
            "session_id": session_id,
            "uploaded_files": [],
            "code_output": {},
            "search_results": [],
            "expertise_level": expertise_level or "advanced",
        }

    async for event in compiled.astream_events(input_state, config=config, version="v2"):
        kind = event.get("event", "")

        # Stream node completions as SSE events
        if kind == "on_chain_end" and event.get("name") in _graph.nodes:
            node_name = event["name"]
            output = event.get("data", {}).get("output", {})

            # Extract the AI message content if present
            messages = output.get("messages", [])
            for msg in messages:
                content = getattr(msg, "content", "")
                if content:
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "node": node_name,
                            "content": content,
                            "phase": output.get("current_phase", ""),
                        }),
                    }

            # Emit phase change if applicable
            new_phase = output.get("current_phase")
            if new_phase:
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

    async def event_generator():
        try:
            async for event in _stream_graph(
                body.message, session_id, request, body.expertise_level,
            ):
                yield event
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

    return EventSourceResponse(event_generator())
