from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# --- API Request schemas ---


class UploadedFile(BaseModel):
    filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=127)
    extracted_text: str = Field(..., max_length=100_000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expertise_level: str | None = Field(
        default=None,
        pattern=r"^(simple|advanced)$",
        description="User expertise level: 'simple' for plain language, 'advanced' for full technical detail. Omit to keep existing.",
    )
    uploaded_files: list[UploadedFile] = Field(
        default_factory=list,
        max_length=10,
        description="Files uploaded by the user (text already extracted).",
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
    has_tables: bool = False
    extraction_quality: Literal["full", "partial", "metadata_only", "empty"] = "full"
    warning: str | None = None


class SessionEndResponse(BaseModel):
    session_id: str
    ended_at: datetime


class SummaryResponse(BaseModel):
    session_id: str
    summary_text: str
    generated_at: datetime


class EvaluationRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    comment: str = Field(default="", max_length=2000, description="Optional feedback comment")


class EvaluationResponse(BaseModel):
    session_id: str
    rating: int
    comment: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    db: bool
    version: str = "0.1.0"


# --- Saved Projects (session metadata) ---


class ProjectListItem(BaseModel):
    session_id: str
    name: str | None = None
    description: str | None = None
    current_phase: str = "orchestrator"
    created_at: datetime
    updated_at: datetime | None = None
    ended_at: datetime | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]
    total: int


class ProjectUpdateRequest(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdateResponse(BaseModel):
    session_id: str
    name: str
    description: str | None = None
    updated_at: datetime


class MessageItem(BaseModel):
    role: str
    content: str
    node: str | None = None
    phase: str | None = None
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageItem]
