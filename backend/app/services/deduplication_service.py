"""Conservative, deterministic deduplication of canonical job offers."""
from collections.abc import Iterable
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from app.domain.job_offer import JobOffer


def _text_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    return normalized or None


def _url_key(value: str | None) -> str | None:
    """Normalize URL details that do not normally change an offer's identity.

    Query strings, fragments, path case, and path parameters are retained.
    Invalid or credential-bearing URLs are deliberately not used as evidence.
    """
    if not value:
        return None
    try:
        parts = urlsplit(str(value))
        if parts.scheme.casefold() not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        port = parts.port
        host = parts.hostname.casefold()
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        if port is not None and not (
            (parts.scheme.casefold() == "http" and port == 80)
            or (parts.scheme.casefold() == "https" and port == 443)
        ):
            host = f"{host}:{port}"
        path = parts.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.casefold(), host, path, parts.query, parts.fragment))
    except (TypeError, ValueError):
        return None


def _location_values(offer: JobOffer) -> frozenset[str]:
    fields = (
        *offer.location.locations,
        *offer.location.cities,
        *offer.location.countries,
        *offer.location.location_restrictions,
        *offer.location.timezone_restrictions,
    )
    return frozenset(key for value in fields if (key := _text_key(value)))


def _cross_source_key(offer: JobOffer) -> tuple[str, str, frozenset[str]] | None:
    company = _text_key(offer.company.name)
    title = _text_key(offer.position.title)
    locations = _location_values(offer)
    if not company or not title or not locations:
        return None
    return company, title, locations


class DeduplicationService:
    """Keep the first offer when stable evidence identifies a duplicate.

    The matching rules are exact source identity, conservatively normalized
    offer URL, then exact company/title plus an overlapping explicit location
    across different sources. No field values are merged or mutated.
    """

    def deduplicate(self, offers: Iterable[JobOffer]) -> list[JobOffer]:
        unique: list[JobOffer] = []
        source_ids: set[tuple[str, str]] = set()
        urls: set[str] = set()
        cross_source: dict[tuple[str, str], list[tuple[str, frozenset[str]]]] = {}

        for offer in offers:
            source_name = _text_key(offer.source.name)
            source_id = offer.identity.source_id.strip() if offer.identity.source_id else None
            source_id = source_id or None
            identity_key = (source_name, source_id) if source_name and source_id else None
            url_key = _url_key(str(offer.identity.offer_url)) if offer.identity.offer_url else None
            cross_key = _cross_source_key(offer)

            duplicate = identity_key is not None and identity_key in source_ids
            duplicate = duplicate or (url_key is not None and url_key in urls)
            if not duplicate and cross_key is not None and source_name is not None:
                company, title, locations = cross_key
                duplicate = any(
                    prior_source != source_name and bool(prior_locations & locations)
                    for prior_source, prior_locations in cross_source.get((company, title), [])
                )

            if duplicate:
                continue

            unique.append(offer)
            if identity_key is not None:
                source_ids.add(identity_key)
            if url_key is not None:
                urls.add(url_key)
            if cross_key is not None and source_name is not None:
                company, title, locations = cross_key
                cross_source.setdefault((company, title), []).append((source_name, locations))

        return unique
