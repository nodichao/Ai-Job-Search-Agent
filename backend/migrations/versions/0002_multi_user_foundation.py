"""Multi-user database foundation: users, auth_sessions, user-scoped settings/shortlist.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_SETTINGS_TABLE = "user_settings"
SHORTLIST_ENTRIES_TABLE = "shortlist_entries"


def upgrade() -> None:
    """Prepare the multi-user database foundation without touching existing data.

    - Create the `users` table (foundation only; credential fields come later).
    - Create the future `auth_sessions` table.
    - Evolve `user_settings` to the composite key `(user_id, setting_key)`.
    - Evolve `shortlist_entries` to per-owner uniqueness keys.
    - Copy existing rows unchanged (user_id stays NULL for pre-existing data).
    """
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.String(), nullable=True),
        sa.Column("last_used_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_auth_sessions_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_auth_sessions_user_id", "user_id"),
        sa.Index("ix_auth_sessions_token_hash", "token_hash"),
        sa.Index("ix_auth_sessions_expires_at", "expires_at"),
    )

    # --- user_settings: composite key (user_id, setting_key) ---
    op.create_table(
        "user_settings_new",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("setting_key", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("user_id", "setting_key"),
        sa.CheckConstraint("setting_key IN ('profile', 'preferences')", name="ck_user_settings_setting_key"),
    )
    op.create_index(op.f("ix_user_settings_setting_key"), "user_settings_new", ["setting_key"])
    op.create_index(op.f("ix_user_settings_user_id"), "user_settings_new", ["user_id"])
    op.execute(
        "INSERT INTO user_settings_new (user_id, setting_key, payload_json, updated_at) "
        "SELECT NULL, setting_key, payload_json, updated_at FROM user_settings"
    )
    op.drop_table(USER_SETTINGS_TABLE)
    op.rename_table("user_settings_new", USER_SETTINGS_TABLE)

    # --- shortlist_entries: per-owner uniqueness keys ---
    op.create_table(
        "shortlist_entries_new",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("identity_key", sa.String(), nullable=False),
        sa.Column("source_identity", sa.String(), nullable=True),
        sa.Column("canonical_identity", sa.String(), nullable=True),
        sa.Column("offer_url", sa.String(), nullable=True),
        sa.Column("source_slug", sa.String(), nullable=True),
        sa.Column("offer_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "identity_key"),
        sa.UniqueConstraint("user_id", "source_identity"),
        sa.UniqueConstraint("user_id", "canonical_identity"),
        sa.UniqueConstraint("user_id", "offer_url"),
        sa.UniqueConstraint("user_id", "source_slug"),
        sa.CheckConstraint(
            "status IN ('SAVED', 'INTERESTED', 'APPLYING', 'APPLIED', 'REJECTED', 'ARCHIVED')",
            name="ck_shortlist_entries_status",
        ),
    )
    op.create_index(op.f("ix_shortlist_entries_user_id"), "shortlist_entries_new", ["user_id"])
    op.execute(
        "INSERT INTO shortlist_entries_new (id, user_id, identity_key, source_identity, canonical_identity, "
        "offer_url, source_slug, offer_json, status, created_at, updated_at) "
        "SELECT id, NULL, identity_key, source_identity, canonical_identity, offer_url, source_slug, "
        "offer_json, status, created_at, updated_at FROM shortlist_entries"
    )
    op.drop_table(SHORTLIST_ENTRIES_TABLE)
    op.rename_table("shortlist_entries_new", SHORTLIST_ENTRIES_TABLE)


def _count_rows(table: str) -> int:
    return op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()


def _refuse_if_user_scoped_data_exists() -> None:
    """Refuse the downgrade when reverting would lose user-scoped data."""
    if _count_rows("users") > 0:
        raise RuntimeError("Downgrade from revision 0002 refused: the users table must be empty.")
    if _count_rows("auth_sessions") > 0:
        raise RuntimeError("Downgrade from revision 0002 refused: the auth_sessions table must be empty.")
    user_scoped_settings = op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM user_settings WHERE user_id IS NOT NULL")
    ).scalar()
    if user_scoped_settings > 0:
        raise RuntimeError("Downgrade from revision 0002 refused: user-scoped user_settings rows require an owner user.")
    user_scoped_shortlist = op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM shortlist_entries WHERE user_id IS NOT NULL")
    ).scalar()
    if user_scoped_shortlist > 0:
        raise RuntimeError("Downgrade from revision 0002 refused: user-scoped shortlist_entries rows require an owner user.")


def downgrade() -> None:
    """Restore the pre-0002 table shapes without silent data loss.

    The revert only proceeds when no user-owned data blocks the restoration.
    """
    _refuse_if_user_scoped_data_exists()

    # Restore shortlist_entries to its pre-0002 shape.
    op.create_table(
        "shortlist_entries_old",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("identity_key", sa.String(), nullable=False),
        sa.Column("source_identity", sa.String(), nullable=True),
        sa.Column("canonical_identity", sa.String(), nullable=True),
        sa.Column("offer_url", sa.String(), nullable=True),
        sa.Column("source_slug", sa.String(), nullable=True),
        sa.Column("offer_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("identity_key"),
        sa.UniqueConstraint("source_identity"),
        sa.UniqueConstraint("canonical_identity"),
        sa.UniqueConstraint("offer_url"),
        sa.UniqueConstraint("source_slug"),
        sa.CheckConstraint(
            "status IN ('SAVED', 'INTERESTED', 'APPLYING', 'APPLIED', 'REJECTED', 'ARCHIVED')",
            name="ck_shortlist_entries_status",
        ),
    )
    op.execute(
        "INSERT INTO shortlist_entries_old (id, identity_key, source_identity, canonical_identity, offer_url, "
        "source_slug, offer_json, status, created_at, updated_at) "
        "SELECT id, identity_key, source_identity, canonical_identity, offer_url, source_slug, offer_json, "
        "status, created_at, updated_at FROM shortlist_entries"
    )
    op.drop_table("shortlist_entries")
    op.rename_table("shortlist_entries_old", "shortlist_entries")

    # Restore user_settings to its pre-0002 shape.
    op.create_table(
        "user_settings_old",
        sa.Column("setting_key", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("setting_key"),
        sa.CheckConstraint("setting_key IN ('profile', 'preferences')", name="ck_user_settings_setting_key"),
    )
    op.execute(
        "INSERT INTO user_settings_old (setting_key, payload_json, updated_at) "
        "SELECT setting_key, payload_json, updated_at FROM user_settings"
    )
    op.drop_table("user_settings")
    op.rename_table("user_settings_old", "user_settings")

    op.drop_table("auth_sessions")
    op.drop_table("users")
