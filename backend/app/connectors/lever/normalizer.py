"""Normalize only fields established for Lever postings in project references."""
from typing import Any

from app.connectors.base import RawOffer
from app.core.errors import NormalizationError
from app.domain.job_offer import EmploymentType, JobOffer, OfferIdentity, OfferLocation, OfferSource, Position, Employment


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _employment_type(value: Any) -> EmploymentType:
    normalized = _text(value)
    if normalized is None:
        return EmploymentType.UNKNOWN
    key = normalized.casefold().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())
    mapping = {
        "full time": EmploymentType.FULL_TIME,
        "part time": EmploymentType.PART_TIME,
        "contract": EmploymentType.CONTRACT,
        "freelance": EmploymentType.FREELANCE,
        "internship": EmploymentType.INTERNSHIP,
        "temporary": EmploymentType.TEMPORARY,
    }
    return mapping.get(key, EmploymentType.UNKNOWN)


class LeverNormalizer:
    def normalize(self, raw_offer: RawOffer) -> JobOffer:
        if raw_offer.source_name != "Lever":
            raise NormalizationError("LeverNormalizer received an offer from another source")
        payload = raw_offer.payload
        title = _text(payload.get("text"))
        if title is None:
            raise NormalizationError("Lever posting has no usable text/title")

        categories = payload.get("categories")
        categories = categories if isinstance(categories, dict) else {}
        locations = _strings(categories.get("allLocations"))
        primary_location = _text(categories.get("location"))
        if primary_location is not None and primary_location not in locations:
            locations.insert(0, primary_location)

        company_name = _text(raw_offer.provenance.get("company_name"))
        try:
            return JobOffer(
                identity=OfferIdentity(sourceId=raw_offer.source_id),
                source=OfferSource(
                    name="Lever",
                    url="https://api.lever.co/",
                    retrievedAt=raw_offer.retrieved_at,
                ),
                position=Position(title=title),
                company={"name": company_name},
                location=OfferLocation(locations=locations, remote=None),
                employment=Employment(
                    type=_employment_type(categories.get("commitment")),
                    department=_text(categories.get("department")),
                    team=_text(categories.get("team")),
                ),
            )
        except ValueError as exc:
            raise NormalizationError("Lever posting could not be represented by JobOffer") from exc
