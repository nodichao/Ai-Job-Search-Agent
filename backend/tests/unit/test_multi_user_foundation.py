"""Tests for the Phase 1.2.1 multi-user database foundation (Alembic revision 0002)."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
BASELINE_REVISION = "0001"
MULTI_USER_REVISION = "0002"


def _alembic_config(db_path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _upgrade(db_path, revision: str = "head") -> None:
    command.upgrade(_alembic_config(db_path), revision)


def _table_names(db_path) -> set:
    engine = create_engine(f"sqlite:///{db_path}")
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    return tables


def _columns(db_path, table: str) -> set:
    engine = create_engine(f"sqlite:///{db_path}")
    columns = {column["name"] for column in inspect(engine).get_columns(table)}
    engine.dispose()
    return columns


def _indexes(db_path, table: str) -> set:
    engine = create_engine(f"sqlite:///{db_path}")
    indexes = {index["name"] for index in inspect(engine).get_indexes(table)}
    engine.dispose()
    return indexes


def _primary_key_columns(db_path, table: str) -> list:
    engine = create_engine(f"sqlite:///{db_path}")
    primary_key = list(inspect(engine).get_pk_constraint(table)["constrained_columns"])
    engine.dispose()
    return primary_key


def _connect(db_path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def _insert_user(connection: sqlite3.Connection, user_id: str, email: str) -> None:
    connection.execute(
        "INSERT INTO users (id, email, is_active, created_at, updated_at) VALUES (?, ?, 1, '2026-11-03 09:00:00', '2026-11-03 09:00:00')",
        (user_id, email),
    )


def _insert_setting(connection: sqlite3.Connection, user_id: str, setting_key: str, payload_json: str) -> None:
    connection.execute(
        "INSERT INTO user_settings (user_id, setting_key, payload_json, updated_at) VALUES (?, ?, ?, '2026-11-03 09:00:00')",
        (user_id, setting_key, payload_json),
    )


def _insert_session(connection: sqlite3.Connection, session_id: str, user_id: str) -> None:
    connection.execute(
        "INSERT INTO auth_sessions (id, user_id, token_hash, created_at, expires_at, revoked_at, last_used_at) "
        "VALUES (?, ?, 'hashed-token', '2026-11-03 09:00:00', '2027-11-03 09:00:00', NULL, NULL)",
        (session_id, user_id),
    )


def test_upgrade_head_on_fresh_database_creates_multi_user_tables(tmp_path):
    db_path = tmp_path / "fresh.db"
    _upgrade(db_path)

    tables = _table_names(db_path)
    assert {"users", "auth_sessions", "user_settings", "shortlist_entries"} <= tables

    assert {"id", "email", "is_active", "created_at", "updated_at"} <= _columns(db_path, "users")
    assert {"id", "user_id", "token_hash", "created_at", "expires_at", "revoked_at", "last_used_at"} <= _columns(
        db_path, "auth_sessions"
    )
    assert {"user_id", "setting_key", "payload_json", "updated_at"} <= _columns(db_path, "user_settings")
    assert {"id", "user_id", "identity_key", "offer_json", "status", "created_at", "updated_at"} <= _columns(
        db_path, "shortlist_entries"
    )

    assert {"user_id", "setting_key"} == set(_primary_key_columns(db_path, "user_settings"))
    assert "user_id" in _columns(db_path, "shortlist_entries")

    assert {"ix_user_settings_user_id", "ix_user_settings_setting_key"} <= _indexes(db_path, "user_settings")
    assert "ix_shortlist_entries_user_id" in _indexes(db_path, "shortlist_entries")
    assert {"ix_auth_sessions_user_id", "ix_auth_sessions_token_hash", "ix_auth_sessions_expires_at"} <= _indexes(
        db_path, "auth_sessions"
    )


def test_migration_on_historical_base_preserves_existing_data(tmp_path):
    db_path = tmp_path / "historical.db"
    _upgrade(db_path, BASELINE_REVISION)

    # Simulate pre-existing single-user data written directly on the 0001 schema.
    with closing(_connect(db_path)) as connection:
        connection.execute(
            "INSERT INTO user_settings (setting_key, payload_json, updated_at) VALUES ('profile', ?, '2026-11-03 09:00:00')",
            (json.dumps({"skills": ["Python"], "jobTitles": ["Engineer"]}),),
        )
        connection.execute(
            "INSERT INTO user_settings (setting_key, payload_json, updated_at) VALUES ('preferences', ?, '2026-11-03 09:00:00')",
            (json.dumps({}),),
        )
        connection.execute(
            "INSERT INTO shortlist_entries (id, identity_key, source_identity, canonical_identity, offer_url, "
            "source_slug, offer_json, status, created_at, updated_at) "
            "VALUES ('entry-1', 'sourceRemoteOK/source-1', 'sourceRemoteOK/source-1', NULL, NULL, NULL, '{}', 'SAVED', '2026-11-03 09:00:00', '2026-11-03 09:00:00')"
        )
        connection.commit()

    _upgrade(db_path, MULTI_USER_REVISION)

    with closing(_connect(db_path)) as connection:
        settings_rows = connection.execute(
            "SELECT user_id, setting_key, payload_json FROM user_settings ORDER BY setting_key"
        ).fetchall()
        assert len(settings_rows) == 2
        by_key = {row["setting_key"]: row for row in settings_rows}
        assert set(by_key) == {"profile", "preferences"}
        for row in settings_rows:
            assert row["user_id"] is None
        stored_profile = json.loads(by_key["profile"]["payload_json"])
        assert stored_profile["skills"] == ["Python"]
        assert json.loads(by_key["preferences"]["payload_json"]) == {}

        shortlist_rows = connection.execute(
            "SELECT user_id, identity_key, status FROM shortlist_entries"
        ).fetchall()
        assert len(shortlist_rows) == 1
        assert shortlist_rows[0]["user_id"] is None
        assert shortlist_rows[0]["status"] == "SAVED"


def test_multi_user_constraints_allow_independent_scopes(tmp_path):
    db_path = tmp_path / "multiuser.db"
    _upgrade(db_path)

    with closing(_connect(db_path)) as connection:
        _insert_user(connection, "user-1", "owner@example.com")
        _insert_user(connection, "user-2", "second@example.com")

        # Two distinct users may own the same logical setting key.
        _insert_setting(connection, "user-1", "profile", '{"skills": []}')
        _insert_setting(connection, "user-2", "profile", '{"skills": []}')
        connection.commit()

        # The same user cannot own the same setting key twice.
        with pytest.raises(sqlite3.IntegrityError):
            _insert_setting(connection, "user-1", "profile", '{"skills": []}')
        connection.rollback()

        # Email addresses remain unique per user.
        with pytest.raises(sqlite3.IntegrityError):
            _insert_user(connection, "user-1", "owner@example.com")
        connection.rollback()

        # Two distinct users may save the same offer.
        connection.execute(
            "INSERT INTO shortlist_entries (id, user_id, identity_key, source_identity, canonical_identity, "
            "offer_url, source_slug, offer_json, status, created_at, updated_at) "
            "VALUES ('entry-1', 'user-1', 'sourceRemoteOK/source-1', 'sourceRemoteOK/source-1', NULL, NULL, NULL, '{}', 'SAVED', '2026-11-03 09:00:00', '2026-11-03 09:00:00')"
        )
        connection.execute(
            "INSERT INTO shortlist_entries (id, user_id, identity_key, source_identity, canonical_identity, "
            "offer_url, source_slug, offer_json, status, created_at, updated_at) "
            "VALUES ('entry-2', 'user-2', 'sourceRemoteOK/source-1', 'sourceRemoteOK/source-1', NULL, NULL, NULL, '{}', 'SAVED', '2026-11-03 09:00:00', '2026-11-03 09:00:00')"
        )
        connection.commit()

        # The same user cannot save the same offer twice.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO shortlist_entries (id, user_id, identity_key, source_identity, canonical_identity, "
                "offer_url, source_slug, offer_json, status, created_at, updated_at) "
                "VALUES ('entry-3', 'user-1', 'sourceRemoteOK/source-1', 'sourceRemoteOK/source-1', NULL, NULL, NULL, '{}', 'SAVED', '2026-11-03 09:00:00', '2026-11-03 09:00:00')"
            )
        connection.rollback()


def test_auth_sessions_reference_existing_users(tmp_path):
    db_path = tmp_path / "sessions.db"
    _upgrade(db_path)

    with closing(_connect(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _insert_user(connection, "user-1", "owner@example.com")
        _insert_session(connection, "session-1", "user-1")
        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            _insert_session(connection, "session-2", "unknown-user")
        connection.rollback()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM users WHERE id = 'user-1'")
        connection.rollback()

        _insert_user(connection, "user-2", "second@example.com")
        connection.execute("DELETE FROM users WHERE id = 'user-2'")
        connection.commit()


def test_downgrade_from_multi_user_foundation_restores_previous_shape(tmp_path):
    db_path = tmp_path / "downgrade.db"
    _upgrade(db_path)
    command.downgrade(_alembic_config(db_path), BASELINE_REVISION)

    tables = _table_names(db_path)
    assert "users" not in tables
    assert "auth_sessions" not in tables
    assert "user_settings" in tables
    assert "shortlist_entries" in tables
    assert _primary_key_columns(db_path, "user_settings") == ["setting_key"]
    assert "user_id" not in _columns(db_path, "user_settings")


def test_downgrade_refuses_when_user_data_exists(tmp_path):
    db_path = tmp_path / "downgrade_refusal.db"
    _upgrade(db_path)

    with closing(_connect(db_path)) as connection:
        _insert_user(connection, "user-1", "owner@example.com")
        _insert_session(connection, "session-1", "user-1")
        connection.commit()

    with pytest.raises(RuntimeError):
        command.downgrade(_alembic_config(db_path), BASELINE_REVISION)
