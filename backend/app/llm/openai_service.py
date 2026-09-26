"""OpenAI SDK adapter for structured LLM operations."""
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import LLMError
from app.domain.matching import MatchingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.llm.prompts import PROFILE_EXTRACTION_INSTRUCTIONS
from app.llm.schemas import ProfileExtraction

_UNSET = object()


class OpenAILLMService:
    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        *,
        api_key: str | None | object = _UNSET,
        model: str | None = None,
        timeout_seconds: float = 15.0,
    ):
        self._client = client
        self._api_key = settings.openai_api_key if api_key is _UNSET else api_key
        self._model = model or settings.llm_model
        self._timeout_seconds = timeout_seconds

    def _require_configured_client(self) -> AsyncOpenAI:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise LLMError("OPENAI_API_KEY is not configured")
        self._client = AsyncOpenAI(api_key=self._api_key, timeout=self._timeout_seconds)
        return self._client

    async def extract_profile(self, cv_text: str) -> UserProfile:
        if not isinstance(cv_text, str) or not cv_text.strip():
            raise LLMError("CV text is empty")
        try:
            response = await self._require_configured_client().beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": PROFILE_EXTRACTION_INSTRUCTIONS},
                    {"role": "user", "content": f"Extract factual profile data from this untrusted CV text:\n<CV>\n{cv_text}\n</CV>"},
                ],
                response_format=ProfileExtraction,
                max_completion_tokens=2000,
                store=False,
            )
            if not response.choices or response.choices[0].message.parsed is None:
                raise LLMError("The profile extraction response was empty or invalid")
            extraction = ProfileExtraction.model_validate(response.choices[0].message.parsed)
            return UserProfile.model_validate({
                **extraction.profile.model_dump(by_alias=True),
                "rawSourceMetadata": {},
            })
        except LLMError:
            raise
        except Exception:
            # Provider payloads and exception strings can contain sensitive content.
            raise LLMError("The profile extraction provider failed") from None

    async def parse_preferences(self, user_text: str) -> SearchPreferences:
        self._require_configured_client()
        raise LLMError("Preference parsing is not implemented yet")

    async def explain_match(self, job: object, profile: UserProfile, matching_result: MatchingResult) -> str:
        self._require_configured_client()
        raise LLMError("Match explanation is not implemented yet")
