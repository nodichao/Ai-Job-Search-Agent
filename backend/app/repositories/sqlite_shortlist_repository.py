"""SQLite persistence for the unauthenticated, single-user MVP shortlist."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import unquote

from pydantic import ValidationError

from app.core.errors import ShortlistDuplicateError, ShortlistPersistenceError
from app.domain.job_offer import JobOffer
from app.domain.shortlist import ShortlistEntry, ShortlistStatus
from app.repositories.shortlist_repository import ShortlistRepository


class SQLiteShortlistRepository(ShortlistRepository):
    def __init__(self, database_url: str) -> None:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix) or "?" in database_url or "#" in database_url:
            raise ValueError("Shortlist persistence currently requires a file-backed sqlite:/// DATABASE_URL")
        raw_path = unquote(database_url[len(prefix):])
        if not raw_path or raw_path == ":memory:":
            raise ValueError("Shortlist persistence requires a file-backed SQLite database")
        path = Path(raw_path).expanduser()
        self._database_path = path if path.is_absolute() else Path.cwd() / path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection: sqlite3.Connection | None = None
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._database_path, timeout=5.0)
            connection.row_factory = sqlite3.Row
            self._ensure_schema(connection)
            with connection:
                yield connection
        except (sqlite3.Error, OSError) as exc:
            raise ShortlistPersistenceError("Shortlist storage is unavailable") from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS shortlist_entries (
                id TEXT PRIMARY KEY,
                identity_key TEXT NOT NULL UNIQUE,
                source_identity TEXT UNIQUE,
                canonical_identity TEXT UNIQUE,
                offer_url TEXT UNIQUE,
                source_slug TEXT UNIQUE,
                offer_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'SAVED', 'INTERESTED', 'APPLYING', 'APPLIED', 'REJECTED', 'ARCHIVED'
                )),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        connection.commit()

    @staticmethod
    def _serialize_offer(offer: JobOffer) -> str:
        return json.dumps(offer.model_dump(mode="json", by_alias=True), ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _entry(row: sqlite3.Row) -> ShortlistEntry:
        try:
            return ShortlistEntry(
                id=row["id"],
                offer=JobOffer.model_validate(json.loads(row["offer_json"])),
                status=row["status"],
                createdAt=row["created_at"],
                updatedAt=row["updated_at"],
            )
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ShortlistPersistenceError("Stored shortlist data is invalid") from exc

    def add(
        self,
        entry: ShortlistEntry,
        *,
        identity_key: str,
        source_identity: str | None,
        canonical_identity: str | None,
        offer_url: str | None,
        source_slug: str | None,
    ) -> ShortlistEntry:
        conditions = ["identity_key = ?"]
        parameters: list[str] = [identity_key]
        for column, value in (
            ("source_identity", source_identity),
            ("canonical_identity", canonical_identity),
            ("offer_url", offer_url),
            ("source_slug", source_slug),
        ):
            if value is not None:
                conditions.append(f"{column} = ?")
                parameters.append(value)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                f"SELECT id FROM shortlist_entries WHERE {' OR '.join(conditions)} LIMIT 1",
                parameters,
            ).fetchone()
            if duplicate is not None:
                raise ShortlistDuplicateError("Offer is already in the shortlist")
            try:
                connection.execute(
                    """INSERT INTO shortlist_entries
                    (id, identity_key, source_identity, canonical_identity, offer_url, source_slug, offer_json, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entry.id,
                        identity_key,
                        source_identity,
                        canonical_identity,
                        offer_url,
                        source_slug,
                        self._serialize_offer(entry.offer),
                        entry.status.value,
                        entry.created_at.isoformat(),
                        entry.updated_at.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ShortlistDuplicateError("Offer is already in the shortlist") from exc
        return entry

    def list_entries(self) -> list[ShortlistEntry]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, offer_json, status, created_at, updated_at FROM shortlist_entries ORDER BY created_at DESC, id ASC"
            ).fetchall()
            return [self._entry(row) for row in rows]

    def get_entry(self, entry_id: str) -> ShortlistEntry | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, offer_json, status, created_at, updated_at FROM shortlist_entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
            return self._entry(row) if row is not None else None

    def update_status(self, entry_id: str, new_status: ShortlistStatus, updated_at: str) -> ShortlistEntry | None:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE shortlist_entries SET status = ?, updated_at = ? WHERE id = ?",
                (new_status.value, updated_at, entry_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, offer_json, status, created_at, updated_at FROM shortlist_entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
            return self._entry(row) if row is not None else None

    def delete(self, entry_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM shortlist_entries WHERE id = ?", (entry_id,))
            return cursor.rowcount > 0
