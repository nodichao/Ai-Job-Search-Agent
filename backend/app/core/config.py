"""Small environment-driven settings object with no implicit .env loading."""
from dataclasses import dataclass
import os

from app.core.errors import ConfigurationError


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false", "1", "0", "yes", "no"}:
        raise ConfigurationError(f"{name} must be a boolean value")
    return normalized in {"true", "1", "yes"}


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    llm_model: str = "gpt-5.6-luna"
    database_url: str = "sqlite:///./job_agent.db"
    remoteok_enabled: bool = False
    remoteok_endpoint: str = "https://remoteok.com/api"
    himalayas_enabled: bool = True
    lever_enabled: bool = False
    lever_site: str | None = None
    request_timeout_seconds: float = 15.0
    max_results_per_source: int = 100
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
            limit = int(os.getenv("MAX_RESULTS_PER_SOURCE", "100"))
            port = int(os.getenv("PORT", "8000"))
            origins = tuple(item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip())
        except ValueError as exc:
            raise ConfigurationError("Numeric configuration has an invalid value") from exc
        if timeout <= 0 or limit < 1 or not 1 <= port <= 65535:
            raise ConfigurationError("Timeout, result limit, or port is outside its valid range")
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            llm_model=os.getenv("LLM_MODEL", "gpt-5.6-luna"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./job_agent.db"),
            remoteok_enabled=_bool("REMOTEOK_ENABLED", False),
            remoteok_endpoint=os.getenv("REMOTEOK_ENDPOINT", "https://remoteok.com/api").strip(),
            himalayas_enabled=_bool("HIMALAYAS_ENABLED", True),
            lever_enabled=_bool("LEVER_ENABLED", False),
            lever_site=os.getenv("LEVER_SITE") or None,
            request_timeout_seconds=timeout,
            max_results_per_source=limit,
            cors_origins=origins,
            port=port,
        )


settings = Settings.from_env()
