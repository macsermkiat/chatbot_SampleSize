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
    "gap_summarize": ("anthropic", "claude-sonnet-4-6"),
    "methodology":   ("anthropic", "claude-sonnet-4-6"),
    "biostatistics": ("anthropic", "claude-sonnet-4-6"),
    "diagnostic":    ("openai",    "gpt-5-mini"),
    "coding":        ("anthropic", "claude-sonnet-4-6"),
}

_FALLBACK_MODEL = "gemini-3-flash-preview"


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------

def _build_openai(model: str, *, temperature: float = 0.3, timeout: int = 200) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=temperature,
        request_timeout=timeout,
        max_retries=4,
    )


def _build_anthropic(model: str, *, temperature: float = 0.3, timeout: float = 200.0) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        timeout=timeout,
        max_retries=4,
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
def _get_base_model(agent_name: str) -> BaseChatModel:
    """Return the base ChatModel (no fallback) for the agent."""
    if agent_name not in AGENT_MODEL_MAP:
        raise ValueError(
            f"Unknown agent '{agent_name}'. "
            f"Valid agents: {list(AGENT_MODEL_MAP.keys())}"
        )
    provider, model_id = AGENT_MODEL_MAP[agent_name]
    builder = _PROVIDER_BUILDERS[provider]
    return builder(model_id)


@lru_cache(maxsize=1)
def _get_fallback_model() -> BaseChatModel:
    return _build_gemini(_FALLBACK_MODEL)


@lru_cache(maxsize=32)
def get_chat_model(agent_name: str) -> BaseChatModel:
    """Return the correct ChatModel for *agent_name* with a Gemini fallback.

    Use this for plain text (non-structured) LLM calls.
    Raises ``KeyError`` if the agent name is not in AGENT_MODEL_MAP.
    """
    primary = _get_base_model(agent_name)
    fallback = _get_fallback_model()
    return primary.with_fallbacks([fallback])


_structured_cache: dict[tuple[str, str], BaseChatModel] = {}


def get_structured_model(agent_name: str, schema: type) -> BaseChatModel:
    """Return a ChatModel with structured output AND a Gemini fallback.

    Applies ``with_structured_output`` to both the primary and fallback
    models *before* chaining them, so the fallback produces the same
    Pydantic schema if the primary provider is overloaded or errors.
    """
    key = (agent_name, schema.__name__)
    if key not in _structured_cache:
        primary = _get_base_model(agent_name).with_structured_output(schema)
        fallback = _get_fallback_model().with_structured_output(schema)
        _structured_cache[key] = primary.with_fallbacks([fallback])
    return _structured_cache[key]


def extract_token_usage(response) -> dict:
    """Extract token usage from a LangChain response object.

    Returns a dict with prompt_tokens, completion_tokens, total_tokens, and model.
    All values default to 0 / None if unavailable.
    """
    usage: dict = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "model": None,
    }

    # Try usage_metadata first (LangChain standard).
    # In newer LangChain versions, usage_metadata is a UsageMetadata object
    # (not a plain dict), so we accept any mapping-like object with .get().
    um = getattr(response, "usage_metadata", None)
    if um is not None:
        _get = getattr(um, "get", None) or (lambda k, d=0: getattr(um, k, d))
        usage["prompt_tokens"] = _get("input_tokens", 0) or _get("prompt_tokens", 0)
        usage["completion_tokens"] = _get("output_tokens", 0) or _get("completion_tokens", 0)
        usage["total_tokens"] = _get("total_tokens", 0)

    # Fallback to response_metadata
    if usage["total_tokens"] == 0:
        rm = getattr(response, "response_metadata", {}) or {}
        token_usage = rm.get("token_usage") or rm.get("usage") or {}
        if token_usage:
            usage["prompt_tokens"] = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0)
            usage["completion_tokens"] = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0)
            usage["total_tokens"] = token_usage.get("total_tokens", 0)
        model_name = rm.get("model_name") or rm.get("model")
        if model_name:
            usage["model"] = model_name

    # Always try to get model name from response_metadata even if usage_metadata worked
    if usage["model"] is None:
        rm = getattr(response, "response_metadata", {}) or {}
        usage["model"] = rm.get("model_name") or rm.get("model")

    if usage["total_tokens"] == 0 and (usage["prompt_tokens"] or usage["completion_tokens"]):
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    if usage["total_tokens"] == 0:
        _logger.debug(
            "Token extraction returned zeros for response type=%s, attrs=%s",
            type(response).__name__,
            [a for a in dir(response) if not a.startswith("_")],
        )

    return usage
