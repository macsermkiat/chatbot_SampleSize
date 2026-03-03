"""LangGraph state definition and structured output schemas."""

from __future__ import annotations

from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Shared graph state
# ---------------------------------------------------------------------------

Phase = Literal[
    "orchestrator",
    "research_gap",
    "methodology",
    "biostatistics",
]

ExpertiseLevel = Literal["simple", "advanced"]


class ResearchState(TypedDict):
    """Shared state passed through every node in the LangGraph."""

    # Core message history (LangGraph's add_messages reducer appends)
    messages: Annotated[list[AnyMessage], add_messages]

    # Routing & phase tracking
    current_phase: Phase
    agent_to_route_to: str          # "" = stay in current phase
    forwarded_message: str          # context passed to next agent

    # Flags
    needs_clarification: bool
    need_info: bool                 # biostats-specific: still gathering params

    # Session
    session_id: str

    # File uploads (extracted text from PDF/DOCX/images)
    uploaded_files: list[dict]      # [{filename, mime_type, extracted_text}]

    # Coding agent output (persisted for Supabase/Drive saving)
    code_output: dict               # {language, script, session_id}

    # Search results (Tavily)
    search_results: list[dict]      # [{url, title, content, score}]

    # Loop guard: counts searches executed within a single graph invocation
    search_count: int               # reset to 0 at entry_router

    # User expertise level -- controls prompt tone/depth
    expertise_level: ExpertiseLevel  # "simple" or "advanced" (default "advanced")

    # Code execution state (auto-execute via Code Interpreter)
    execution_result: dict          # {success, stdout, error_message}
    stored_python_script: str       # last generated script (for follow-up code requests)
    has_pending_code: bool          # True when code is available for follow-up


# ---------------------------------------------------------------------------
# Structured output schemas (one per agent family)
# ---------------------------------------------------------------------------

class OrchestratorOutput(BaseModel):
    """Orchestrator / triage node output."""

    direct_response_to_user: str = Field(
        ..., description="Short message to the user acknowledging the route or asking for clarification."
    )
    needs_clarification: bool = Field(
        default=False, description="True if the orchestrator needs more info before routing."
    )
    agent_to_route_to: str = Field(
        default="",
        description=(
            "Route to: 'research_gap', 'methodology', "
            "'biostatistics', or '' to stay. "
            "MUST be '' when needs_clarification is true."
        ),
    )
    forwarded_message: str = Field(
        default="", description="Detailed technical instruction for the next agent."
    )


class GapSearchOutput(BaseModel):
    """ResearchGapAgentSearch returns 3-5 search terms."""

    terms: list[str] = Field(
        ..., description="List of 3-5 search query terms for literature search."
    )


class GapSummarizeOutput(BaseModel):
    """ResearchGapSummarize node output with routing."""

    direct_response_to_user: str
    needs_clarification: bool = Field(
        default=False,
        description="True if you asked the user a question and need their answer before proceeding.",
    )
    agent_to_route_to: str = Field(
        default="",
        description=(
            "Route to: 'research_gap', 'methodology', "
            "'biostatistics', or '' to stay. "
            "MUST be '' when needs_clarification is true."
        ),
    )
    forwarded_message: str = ""


class MethodologyOutput(BaseModel):
    """MethodologyAgent node output with routing."""

    direct_response_to_user: str
    needs_clarification: bool = Field(
        default=False,
        description="True if you asked the user a question and need their answer before proceeding.",
    )
    agent_to_route_to: str = Field(
        default="",
        description=(
            "Route to: 'research_gap', 'methodology', "
            "'biostatistics', or '' to stay. "
            "MUST be '' when needs_clarification is true."
        ),
    )
    forwarded_message: str = ""


class BiostatisticsOutput(BaseModel):
    """BiostatisticsAgent node output."""

    session_id: str = ""
    direct_response_to_user: str
    need_info: bool = Field(
        default=False, description="True if the agent still needs more info from the user."
    )
    diagnostic_query: str = Field(
        default="",
        description=(
            "If non-empty, calls the diagnostic tool with this query to recommend "
            "the appropriate statistical test. Include variable types, distribution, "
            "dependency, and number of groups."
        ),
    )
    forwarded_message: str = Field(
        default="", description="Detailed instruction for the coding agent."
    )


class CodingOutput(BaseModel):
    """CodingAgent node output -- always generates a runnable Python script."""

    session_id: str = ""
    direct_response_to_user: str
    python_script: str = Field(
        default="",
        description="Always generate a runnable Python script that prints results to stdout.",
    )
    agent_to_route_to: str = Field(
        default="",
        description=(
            "Route to another phase: 'research_gap', 'methodology', "
            "'biostatistics', or '' to stay."
        ),
    )
    forwarded_message: str = Field(
        default="", description="Context summary for the next agent."
    )
