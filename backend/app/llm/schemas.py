from pydantic import BaseModel

from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile


class ProfileExtraction(BaseModel):
    profile: UserProfile


class PreferenceExtraction(BaseModel):
    preferences: SearchPreferences


class MatchExplanation(BaseModel):
    explanation: str
