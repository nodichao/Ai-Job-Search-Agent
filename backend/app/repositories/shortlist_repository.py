from typing import Protocol

from app.domain.shortlist import ShortlistEntry, ShortlistStatus


class ShortlistRepository(Protocol):
    def add(
        self,
        entry: ShortlistEntry,
        *,
        identity_key: str,
        source_identity: str | None,
        canonical_identity: str | None,
        offer_url: str | None,
        source_slug: str | None,
    ) -> ShortlistEntry: ...

    def list_entries(self) -> list[ShortlistEntry]: ...

    def get_entry(self, entry_id: str) -> ShortlistEntry | None: ...

    def update_status(self, entry_id: str, new_status: ShortlistStatus, updated_at: str) -> ShortlistEntry | None: ...

    def delete(self, entry_id: str) -> bool: ...
