import pytest

from app.core.errors import PersistenceError
from app.domain.search_preferences import SearchPreferences, PreferenceStrength, SalaryPreference
from app.domain.user_profile import UserProfile
from app.repositories.sqlite_user_settings_repository import SQLiteUserSettingsRepository


def repository(path):
    return SQLiteUserSettingsRepository(f"sqlite:///{path}")


def test_profile_and_preferences_round_trip_independently_after_recreation(tmp_path):
    path = tmp_path / "settings.db"
    first = repository(path)
    profile = UserProfile.model_validate({"skills": ["Python"], "jobTitles": ["Engineer"]})
    preferences = SearchPreferences.model_validate({
        "locations": ["Dakar"],
        "salary": {"minimum": 1000, "currency": "USD"},
        "preferenceStrength": {"locations": "REQUIRED"},
    })

    first.save_profile(profile)
    first.save_preferences(preferences)
    second = repository(path)

    assert second.get_profile() == profile
    assert second.get_preferences() == preferences
    assert second.get_preferences().salary == SalaryPreference(minimum=1000, currency="USD")
    assert second.get_preferences().preference_strength["locations"] is PreferenceStrength.REQUIRED


def test_database_failure_is_wrapped_without_exposing_path(tmp_path):
    path = tmp_path / "not-a-database"
    path.mkdir()
    with pytest.raises(PersistenceError, match="storage is unavailable") as error:
        repository(path).get_profile()
    assert str(tmp_path) not in str(error.value)
