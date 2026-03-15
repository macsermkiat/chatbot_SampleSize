from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_gemini_api_key: str = ""

    # Search
    tavily_api_key: str = ""

    # Database (Supabase or local PostgreSQL)
    database_url: str = ""
    database_url_sync: str = ""

    # Storage (optional)
    supabase_url: str = ""
    supabase_key: str = ""
    google_drive_credentials: str = ""

    # Auth (Supabase)
    supabase_jwt_secret: str = ""

    # Billing (LemonSqueezy)
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_store_id: str = ""
    lemonsqueezy_webhook_secret: str = ""

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def has_database(self) -> bool:
        """True when a database URL is configured."""
        return bool(self.database_url)

    @property
    def database_dsn(self) -> str:
        """Return a plain ``postgresql://`` DSN suitable for asyncpg/psycopg."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()


def validate_required_keys() -> list[str]:
    """Return a list of warnings for missing API keys. Called at startup."""
    warnings: list[str] = []
    if not settings.openai_api_key:
        warnings.append("OPENAI_API_KEY is not set -- OpenAI agents will fail")
    if not settings.anthropic_api_key:
        warnings.append("ANTHROPIC_API_KEY is not set -- Anthropic agents will fail")
    if not settings.tavily_api_key:
        warnings.append("TAVILY_API_KEY is not set -- literature search will fail")
    return warnings
