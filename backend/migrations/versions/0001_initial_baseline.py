"""Initial baseline schema for user_settings and shortlist_entries

Revision ID: 0001
Revises:
Create Date: 2026-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_SETTINGS_TABLE = "user_settings"
SHORTLIST_ENTRIES_TABLE = "shortlist_entries"


def _existing_tables(bind) -> set:
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    """Create the baseline tables when they do not already exist.

    Existing SQLite databases that already contain these tables are adopted
    as-is: the migration is intentionally idempotent and never drops or
    recreates data-bearing tables.
    """
    bind = op.get_bind()
    existing = _existing_tables(bind)
    if USER_SETTINGS_TABLE not in existing:
        op.create_table(
            "user_settings",
            sa.Column("setting_key", sa.String(length=255), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column(
                "updated_at",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("setting_key"),
            sa.CheckConstraint(
                "setting_key IN ('profile', 'preferences')",
                name="ck_user_settings_setting_key",
            ),
        )
    if SHORTLIST_ENTRIES_TABLE not in existing:
        op.create_table(
            "shortlist_entries",
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


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS shortlist_entries")
    op.execute("DROP TABLE IF EXISTS user_settings")
