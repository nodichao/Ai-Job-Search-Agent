"""SQLite persistence for the single user's profile and search preferences."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TypeVar
from urllib.parse import unquote

from pydantic import BaseModel, ValidationError

from app.core.errors import PersistenceError
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.repositories.user_settings_repository import UserSettingsRepository

T = TypeVar("T", bound=BaseModel)


class SQLiteUserSettingsRepository(UserSettingsRepository):
    def __init__(self, database_url: str) -> None:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix) or "?" in database_url or "#" in database_url:
            raise ValueError("User settings persistence requires a file-backed sqlite:/// DATABASE_URL")
        raw_path = unquote(database_url[len(prefix):])
        if not raw_path or raw_path == ":memory:":
            raise ValueError("User settings persistence requires file-backed SQLite")
        path = Path(raw_path).expanduser()
        self._database_path = path if path.is_absolute() else Path.cwd() / path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection: sqlite3.Connection | None = None
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._database_path, timeout=5.0)
            connection.row_factory = sqlite3.Row
            connection.execute(
                """CREATE TABLE IF NOT EXISTS user_settings (
                    setting_key TEXT PRIMARY KEY CHECK(setting_key IN ('profile', 'preferences')),
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.commit()
            with connection:
                yield connection
        except (sqlite3.Error, OSError) as exc:
            raise PersistenceError("User settings storage is unavailable") from exc
        finally:
            if connection is not None:
                connection.close()

    def _get(self, key: str, model: type[T]) -> T | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM user_settings WHERE setting_key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        try:
            return model.model_validate(json.loads(row["payload_json"]))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise PersistenceError("Stored user settings are invalid") from exc

    def _save(self, key: str, value: BaseModel) -> None:
        payload = json.dumps(value.model_dump(mode="json", by_alias=True), ensure_ascii=False, separators=(",", ":"))
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO user_settings (setting_key, payload_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(setting_key) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = CURRENT_TIMESTAMP""",
                (key, payload),
            )

    def get_profile(self) -> UserProfile | None:
        return self._get("profile", UserProfile)

    def save_profile(self, profile: UserProfile) -> UserProfile:
        self._save("profile", profile)
        return profile

    def get_preferences(self) -> SearchPreferences | None:
        return self._get("preferences", SearchPreferences)

    def save_preferences(self, preferences: SearchPreferences) -> SearchPreferences:
        self._save("preferences", preferences)
        return preferences
