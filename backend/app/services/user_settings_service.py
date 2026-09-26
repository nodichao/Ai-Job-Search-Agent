from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.repositories.user_settings_repository import UserSettingsRepository

M = TypeVar("M", bound=BaseModel)


class UserSettingsService:
    def __init__(self, repository: UserSettingsRepository) -> None:
        self._repository = repository

    def get_profile(self) -> UserProfile | None:
        return self._repository.get_profile()

    def replace_profile(self, profile: UserProfile) -> UserProfile:
        return self._repository.save_profile(profile)

    def patch_profile(self, changes: dict[str, Any]) -> UserProfile:
        return self._patch(self.get_profile(), changes, UserProfile, self.replace_profile)

    def get_preferences(self) -> SearchPreferences | None:
        return self._repository.get_preferences()

    def replace_preferences(self, preferences: SearchPreferences) -> SearchPreferences:
        return self._repository.save_preferences(preferences)

    def patch_preferences(self, changes: dict[str, Any]) -> SearchPreferences:
        return self._patch(self.get_preferences(), changes, SearchPreferences, self.replace_preferences)

    @staticmethod
    def _patch(
        current: M | None,
        changes: dict[str, Any],
        model: type[M],
        save: Callable[[M], M],
    ) -> M:
        if current is None:
            raise LookupError("Settings have not been saved")
        if not changes:
            raise ValueError("At least one field must be provided")
        merged = current.model_dump(mode="python", by_alias=True)
        for key, value in changes.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return save(model.model_validate(merged))
