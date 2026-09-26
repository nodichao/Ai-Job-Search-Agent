"""OpenAI SDK adapter boundary. Provider calls are intentionally not implemented in Task 1."""
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import LLMError
from app.domain.matching import MatchingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile


class OpenAILLMService:
    def __init__(self, client: AsyncOpenAI | None = None):
        self._client = client

    def _require_configured_client(self) -> AsyncOpenAI:
        if self._client is not None:
            return self._client
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY is not configured")
        return AsyncOpenAI(api_key=settings.openai_api_key)

    async def extract_profile(self, cv_text: str) -> UserProfile:
        self._require_configured_client()
        raise LLMError("Profile extraction is not implemented yet")

    async def parse_preferences(self, user_text: str) -> SearchPreferences:
        self._require_configured_client()
        raise LLMError("Preference parsing is not implemented yet")

    async def explain_match(self, job: object, profile: UserProfile, matching_result: MatchingResult) -> str:
        self._require_configured_client()
        raise LLMError("Match explanation is not implemented yet")
