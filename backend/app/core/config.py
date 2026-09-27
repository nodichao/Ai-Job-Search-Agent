"""Environment-driven application settings."""
from dataclasses import dataclass
import math
import os
from pathlib import Path
from dotenv import load_dotenv
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
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    database_url: str = "sqlite:///./job_agent.db"
    remoteok_enabled: bool = False
    remoteok_endpoint: str = "https://remoteok.com/api"
    himalayas_enabled: bool = True
    lever_enabled: bool = False
    lever_site: str | None = None
    request_timeout_seconds: float = 15.0
    max_results_per_source: int = 100
    recommendation_score_threshold: float = 60.0
    recommendation_minimum_confidence: float = 0.5
    agent_max_explanations: int = 5
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
            limit = int(os.getenv("MAX_RESULTS_PER_SOURCE", "100"))
            score_threshold = float(os.getenv("RECOMMENDATION_SCORE_THRESHOLD", "60"))
            minimum_confidence = float(os.getenv("RECOMMENDATION_MINIMUM_CONFIDENCE", "0.5"))
            port = int(os.getenv("PORT", "8000"))
            max_explanations = int(os.getenv("AGENT_MAX_EXPLANATIONS", "5"))
            origins = tuple(item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip())
        except ValueError as exc:
            raise ConfigurationError("Numeric configuration has an invalid value") from exc
        if (timeout <= 0 or limit < 1 or not 1 <= port <= 65535
                or not math.isfinite(score_threshold) or not 0 <= score_threshold <= 100
                or not math.isfinite(minimum_confidence) or not 0 <= minimum_confidence <= 1
                or max_explanations < 1):
            raise ConfigurationError("Timeout, result limit, port, or recommendation policy is outside its valid range")
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./job_agent.db"),
            remoteok_enabled=_bool("REMOTEOK_ENABLED", False),
            remoteok_endpoint=os.getenv("REMOTEOK_ENDPOINT", "https://remoteok.com/api").strip(),
            himalayas_enabled=_bool("HIMALAYAS_ENABLED", True),
            lever_enabled=_bool("LEVER_ENABLED", False),
            lever_site=os.getenv("LEVER_SITE") or None,
            request_timeout_seconds=timeout,
            max_results_per_source=limit,
            recommendation_score_threshold=score_threshold,
            recommendation_minimum_confidence=minimum_confidence,
            agent_max_explanations=max_explanations,
            cors_origins=origins,
            port=port,
        )


def load_settings(dotenv_path: Path | None = None) -> Settings:
    """Load backend environment defaults, then construct validated settings.

    Existing process environment values take precedence over values in `.env`.
    """
    path = dotenv_path or Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=path, override=False)
    return Settings.from_env()


settings = load_settings()
