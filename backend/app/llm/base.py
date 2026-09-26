from typing import Protocol

from app.domain.matching import MatchingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile


class LLMService(Protocol):
    async def extract_profile(self, cv_text: str) -> UserProfile: ...
    async def parse_preferences(self, user_text: str) -> SearchPreferences: ...
    async def explain_match(self, job: object, profile: UserProfile, matching_result: MatchingResult) -> str: ...
