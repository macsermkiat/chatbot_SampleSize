from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- API Request schemas ---


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expertise_level: str = Field(
        default="advanced",
        pattern=r"^(simple|advanced)$",
        description="User expertise level: 'simple' for plain language, 'advanced' for full technical detail.",
    )


class SessionCreate(BaseModel):
    """Empty body -- server generates the session."""
    pass


# --- API Response schemas ---


class ChatEvent(BaseModel):
    """Single SSE event sent to the frontend."""
    event: str  # "message" | "phase_change" | "progress" | "code" | "error" | "done"
    data: dict


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    current_phase: str = "orchestrator"


class FileUploadResponse(BaseModel):
    filename: str
    mime_type: str
    extracted_text: str
    char_count: int


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    db: bool
    version: str = "0.1.0"
