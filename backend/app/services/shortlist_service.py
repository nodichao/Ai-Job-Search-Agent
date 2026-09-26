"""Application operations for a user's persistent shortlist."""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from app.core.errors import ShortlistIdentityError
from app.domain.job_offer import JobOffer
from app.domain.shortlist import ShortlistEntry, ShortlistStatus
from app.repositories.shortlist_repository import ShortlistRepository


@dataclass(frozen=True)
class _IdentityKeys:
    primary: str
    source_identity: str | None
    canonical_identity: str | None
    offer_url: str | None
    source_slug: str | None


class ShortlistService:
    def __init__(self, repository: ShortlistRepository) -> None:
        self._repository = repository

    def add(self, offer: JobOffer) -> ShortlistEntry:
        keys = _identity_keys(offer)
        now = datetime.now(timezone.utc)
        entry = ShortlistEntry(
            id=str(uuid4()), offer=offer, status=ShortlistStatus.SAVED,
            createdAt=now, updatedAt=now,
        )
        return self._repository.add(
            entry,
            identity_key=keys.primary,
            source_identity=keys.source_identity,
            canonical_identity=keys.canonical_identity,
            offer_url=keys.offer_url,
            source_slug=keys.source_slug,
        )

    def list(self) -> list[ShortlistEntry]:
        return self._repository.list_entries()

    def get(self, entry_id: str) -> ShortlistEntry | None:
        return self._repository.get_entry(entry_id)

    def update_status(self, entry_id: str, status: ShortlistStatus) -> ShortlistEntry | None:
        return self._repository.update_status(entry_id, status, datetime.now(timezone.utc).isoformat())

    def delete(self, entry_id: str) -> bool:
        return self._repository.delete(entry_id)


def _identity_keys(offer: JobOffer) -> _IdentityKeys:
    source = offer.source.name.strip().casefold()
    if not source:
        raise ShortlistIdentityError("Offer source name is required for shortlist identity")

    source_id = _clean(offer.identity.source_id)
    url = _normalize_url(str(offer.identity.offer_url)) if offer.identity.offer_url else None
    slug = _clean(offer.identity.slug)
    canonical_id = _clean(offer.identity.id)

    source_identity = _key("sourceId", source, source_id) if source_id else None
    source_slug = _key("slug", source, slug) if slug else None
    url_key = _key("offerUrl", "", url) if url else None
    canonical_key = _key("id", source, canonical_id) if canonical_id else None
    primary = source_identity or url_key or source_slug or canonical_key
    if primary is None:
        raise ShortlistIdentityError("Offer needs a source ID, offer URL, slug, or canonical ID to be saved")
    return _IdentityKeys(primary, source_identity, canonical_key, url_key, source_slug)


def _clean(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def _key(kind: str, source: str, value: str) -> str:
    return json.dumps([kind, source, value], ensure_ascii=False, separators=(",", ":"))


def _normalize_url(value: str) -> str:
    parts = urlsplit(value)
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), parts.path, query, ""))
