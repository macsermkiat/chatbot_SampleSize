"""Evaluation framework configuration."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class EvalConfig(BaseSettings):
    """Central configuration for the evaluation pipeline."""

    # -- API Endpoints --
    chatbot_api_url: str = "http://localhost:8000/api/chat"
    chatbot_session_url: str = "http://localhost:8000/api/sessions"

    # -- GPT-5 Comparison --
    openai_api_key: str = Field(default="", description="OpenAI API key for GPT-5 comparison")
    comparison_model: str = "gpt-5.4"
    comparison_temperature: float = 0.7

    # -- LLM Judge --
    judge_provider: Literal["anthropic", "openai"] = "anthropic"
    judge_model: str = "claude-sonnet-4-6"
    judge_temperature: float = 0.3
    judge_runs_per_case: int = 3
    judge_consistency_threshold: float = 0.85
    anthropic_api_key: str = Field(default="", description="Anthropic API key for judge")

    # -- Evaluation Parameters --
    random_seed: int = 42
    expertise_levels: list[str] = ["simple", "advanced"]
    output_dir: str = "evaluation/output"
    raw_responses_dir: str = "evaluation/output/raw_responses"
    judge_results_dir: str = "evaluation/output/judge_results"
    analysis_dir: str = "evaluation/output/analysis"
    reports_dir: str = "evaluation/output/reports"

    # -- Simulated User --
    use_simulated_user: bool = True
    simulated_user_model: str = "gpt-5.4-nano"
    max_conversation_turns: int = 10

    # -- Timeouts --
    chatbot_timeout_seconds: int = 120
    gpt5_timeout_seconds: int = 60
    code_execution_timeout_seconds: int = 30

    model_config = {"env_prefix": "EVAL_", "env_file": ".env", "extra": "ignore"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.openai_api_key:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
