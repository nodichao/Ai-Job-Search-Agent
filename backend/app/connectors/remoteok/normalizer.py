"""Translate RemoteOK's observed JSON fields into the canonical JobOffer."""
from datetime import datetime
from math import isfinite
from typing import Any

from pydantic import HttpUrl, TypeAdapter, ValidationError

from app.connectors.base import RawOffer
from app.core.errors import NormalizationError
from app.domain.job_offer import (
    Application,
    Compensation,
    CompensationComponent,
    CompensationType,
    Company,
    JobOffer,
    OfferDates,
    OfferIdentity,
    OfferLocation,
    OfferSource,
    Position,
)

_URL_ADAPTER = TypeAdapter(HttpUrl)


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _url(value: Any) -> HttpUrl | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return _URL_ADAPTER.validate_python(value.strip())
    except ValidationError:
        return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if isfinite(result) and result >= 0 else None


def _published_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


class RemoteOKNormalizer:
    def normalize(self, raw_offer: RawOffer) -> JobOffer:
        if raw_offer.source_name != "RemoteOK":
            raise NormalizationError("RemoteOKNormalizer received an offer from another source")
        payload = raw_offer.payload

        title = _text(payload.get("position"))
        if title is None:
            raise NormalizationError("RemoteOK offer has no usable position/title")

        tags_value = payload.get("tags")
        categories = [tag.strip() for tag in tags_value if isinstance(tag, str) and tag.strip()] if isinstance(tags_value, list) else []
        location_text = _text(payload.get("location"))
        locations = [location_text] if location_text is not None else []

        minimum = _number(payload.get("salary_min"))
        maximum = _number(payload.get("salary_max"))
        compensation = None
        if minimum is not None or maximum is not None:
            compensation = Compensation(
                components=[
                    CompensationComponent(
                        type=CompensationType.UNKNOWN,
                        min=minimum,
                        max=maximum,
                    )
                ]
            )

        company_name = _text(payload.get("company"))
        try:
            return JobOffer(
                identity=OfferIdentity(
                    sourceId=raw_offer.source_id,
                    slug=_text(payload.get("slug")),
                    offerUrl=_url(payload.get("url")),
                ),
                source=OfferSource(
                    name=raw_offer.source_name,
                    url=_url(raw_offer.provenance.get("source_url")),
                    retrievedAt=raw_offer.retrieved_at,
                ),
                position=Position(
                    title=title,
                    description=_text(payload.get("description")),
                    # RemoteOK exposes tags, but their precise skills taxonomy is
                    # not verified; preserve them as source categories.
                    categories=categories,
                    summary=None,
                ),
                company=Company(
                    name=company_name,
                    logoUrl=_url(payload.get("company_logo")),
                ),
                location=OfferLocation(
                    locations=locations,
                    # A source-level remote-job scope is not proof of individual
                    # offer eligibility or worldwide access.
                    remote=None,
                ),
                compensation=compensation,
                dates=OfferDates(publishedAt=_published_at(payload.get("date"))),
                application=Application(applyUrl=_url(payload.get("apply_url"))),
            )
        except ValidationError as exc:
            raise NormalizationError("RemoteOK offer could not be represented by JobOffer") from exc
