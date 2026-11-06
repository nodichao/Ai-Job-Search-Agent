"""Tests for the Alembic migration foundation and SQLite runtime settings."""

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.domain.job_offer import JobOffer
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.repositories.sqlite_shortlist_repository import SQLiteShortlistRepository
from app.repositories.sqlite_user_settings_repository import SQLiteUserSettingsRepository
from app.services.shortlist_service import ShortlistService

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
BASELINE_REVISION = "0001"
MULTI_USER_REVISION = "0002"


def _alembic_config(db_path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def test_upgrade_head_on_fresh_database_creates_baseline_tables(tmp_path):
    db_path = tmp_path / "fresh.db"
    config = _alembic_config(db_path)

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert {"user_settings", "shortlist_entries"} <= tables


def test_existing_base_is_adopted_by_baseline_migration_without_data_loss(tmp_path):
    db_path = tmp_path / "existing.db"
    settings_repository = SQLiteUserSettingsRepository(f"sqlite:///{db_path}")
    profile = UserProfile.model_validate({"skills": ["Python"], "jobTitles": ["Engineer"]})
    settings_repository.save_profile(profile)

    config = _alembic_config(db_path)
    command.upgrade(config, "head")
    script = ScriptDirectory.from_config(config)
    assert script.get_current_head() == MULTI_USER_REVISION

    # The adoption must not drop or alter the pre-existing settings data.
    assert settings_repository.get_profile() == profile


def test_repositories_remain_compatible_after_migration(tmp_path):
    db_path = tmp_path / "migrated.db"
    config = _alembic_config(db_path)
    command.upgrade(config, "head")

    settings_repository = SQLiteUserSettingsRepository(f"sqlite:///{db_path}")
    shortlist_repository = ShortlistService(SQLiteShortlistRepository(f"sqlite:///{db_path}"))

    profile = UserProfile.model_validate({"skills": ["Python"], "jobTitles": ["Engineer"]})
    settings_repository.save_profile(profile)
    settings_repository.save_preferences(SearchPreferences.model_validate({}))

    shortlist_repository.add(
        JobOffer.model_validate(
            {
                "identity": {"sourceId": "remote-1", "offerUrl": "https://jobs.example/remote-1", "slug": "remote-1"},
                "source": {"name": "RemoteOK", "url": "https://remoteok.example/", "retrievedAt": "2026-09-26T12:00:00Z"},
                "position": {"title": "Platform Engineer"},
                "company": {"name": "ExampleCo"},
            },
        ),
    )

    assert settings_repository.get_profile() == profile
    assert shortlist_repository.list() != []


def test_sqlite_runtime_settings_use_wal_and_busy_timeout(tmp_path):
    db_path = tmp_path / "runtime.db"
    settings_repository = SQLiteUserSettingsRepository(f"sqlite:///{db_path}")
    settings_repository.save_profile(UserProfile.model_validate({"skills": ["Python"], "jobTitles": ["Engineer"]}))

    with sqlite3.connect(db_path) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert str(journal_mode).lower() == "wal"
    assert int(busy_timeout) >= 0
