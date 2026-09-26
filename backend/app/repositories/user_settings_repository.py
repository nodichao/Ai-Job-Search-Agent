from typing import Protocol

from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile


class UserSettingsRepository(Protocol):
    def get_profile(self) -> UserProfile | None: ...

    def save_profile(self, profile: UserProfile) -> UserProfile: ...

    def get_preferences(self) -> SearchPreferences | None: ...

    def save_preferences(self, preferences: SearchPreferences) -> SearchPreferences: ...
