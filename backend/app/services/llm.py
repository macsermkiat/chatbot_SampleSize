"""LLM factory -- returns a ChatModel for any agent by name.

Supports three providers:
  - OpenAI (gpt-5-mini for lightweight tasks)
  - Anthropic (Claude Sonnet 4.6 for complex reasoning / structured synthesis)
  - Google Gemini (fallback for all agents)

Every model is wrapped with a Gemini fallback chain so that transient
provider outages are handled gracefully.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model mapping: agent name -> (provider, model_id)
# ---------------------------------------------------------------------------

AGENT_MODEL_MAP: dict[str, tuple[str, str]] = {
    "orchestrator":  ("openai",    "gpt-5-mini"),
    "gap_search":    ("openai",    "gpt-5-mini"),
    "gap_summarize": ("anthropic", "claude-sonnet-4-6-20250514"),
    "methodology":   ("anthropic", "claude-sonnet-4-6-20250514"),
    "biostatistics": ("anthropic", "claude-sonnet-4-6-20250514"),
    "diagnostic":    ("openai",    "gpt-5-mini"),
    "coding":        ("anthropic", "claude-sonnet-4-6-20250514"),
}

_FALLBACK_MODEL = "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------

def _build_openai(model: str, *, temperature: float = 0.3, timeout: int = 200) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=temperature,
        request_timeout=timeout,
        max_retries=2,
    )


def _build_anthropic(model: str, *, temperature: float = 0.3, timeout: float = 200.0) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        timeout=timeout,
        max_retries=2,
    )


def _build_gemini(model: str, *, temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_gemini_api_key,
        temperature=temperature,
    )


_PROVIDER_BUILDERS = {
    "openai": _build_openai,
    "anthropic": _build_anthropic,
    "gemini": _build_gemini,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def get_chat_model(agent_name: str) -> BaseChatModel:
    """Return the correct ChatModel for *agent_name* with a Gemini fallback.

    Raises ``KeyError`` if the agent name is not in AGENT_MODEL_MAP.
    """
    provider, model_id = AGENT_MODEL_MAP[agent_name]
    builder = _PROVIDER_BUILDERS[provider]
    primary = builder(model_id)

    # Wrap with Gemini fallback for resilience
    fallback = _build_gemini(_FALLBACK_MODEL)
    return primary.with_fallbacks([fallback])
