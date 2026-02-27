"""LLM factory -- returns a ChatModel for any agent by name.

Supports OpenAI (primary) and Google Gemini (fallback for structured-output
parse-error recovery, matching the n8n pattern).
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.agents.prompts import AGENT_MODEL_MAP
from app.config import settings

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_GEMINI_AGENTS = frozenset({"gap_summarize"})


def _build_openai(model: str, *, temperature: float = 0.3, timeout: int = 200) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=temperature,
        request_timeout=timeout,
        max_retries=2,
    )


def _build_gemini(model: str, *, temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_gemini_api_key,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def get_chat_model(agent_name: str) -> BaseChatModel:
    """Return the correct ChatModel for *agent_name*.

    Raises ``KeyError`` if the agent name is not in AGENT_MODEL_MAP.
    """
    model_id = AGENT_MODEL_MAP[agent_name]

    if agent_name in _GEMINI_AGENTS:
        return _build_gemini(model_id)

    return _build_openai(model_id)


def get_fallback_model(agent_name: str) -> BaseChatModel:
    """Return a Gemini model to use when the primary (OpenAI) call fails.

    This mirrors the n8n pattern where Gemini is wired as a fallback for
    structured-output parse errors.
    """
    return _build_gemini("gemini-2.0-flash")
