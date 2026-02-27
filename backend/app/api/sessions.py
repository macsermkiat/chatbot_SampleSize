"""Session API -- CRUD for chat sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db import get_pool
from app.models import SessionResponse

router = APIRouter(prefix="/api", tags=["sessions"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (session_id, created_at, current_phase)
            VALUES ($1, $2, $3)
            ON CONFLICT (session_id) DO NOTHING
            """,
            session_id,
            now,
            "orchestrator",
        )

    return SessionResponse(
        session_id=session_id,
        created_at=now,
        current_phase="orchestrator",
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Retrieve an existing session."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT session_id, created_at, current_phase FROM sessions WHERE session_id = $1",
            session_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    return SessionResponse(
        session_id=row["session_id"],
        created_at=row["created_at"],
        current_phase=row["current_phase"],
    )
