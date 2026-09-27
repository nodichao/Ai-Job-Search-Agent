"""Map documented Himalayas job fields into the canonical JobOffer model."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from math import isfinite
import re
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
    Employment,
    EmploymentType,
    Experience,
    JobOffer,
    OfferDates,
    OfferIdentity,
    OfferLocation,
    OfferSource,
    Position,
    RemoteScope,
    Seniority,
)

_URL = TypeAdapter(HttpUrl)


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _url(value: Any) -> HttpUrl | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return _URL.validate_python(value.strip())
    except ValidationError:
        return None


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style"}:
            self.suppressed += 1
        elif not self.suppressed and tag in {"p", "div", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1
        elif not self.suppressed and tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)


def _description(value: Any) -> str | None:
    value = _text(value)
    if value is None:
        return None
    parser = _TextParser()
    try:
        parser.feed(value)
        parser.close()
    except (AssertionError, ValueError):
        pass
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines()]
    result = "\n".join(line for line in lines if line)
    return result or None


def _date(value: Any) -> datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and isfinite(float(value)):
        try:
            # Project references conflict between ISO strings and Unix
            # timestamps; observed payloads use epoch seconds while the data
            # dictionary also describes millisecond values.
            timestamp = float(value)
            if abs(timestamp) >= 100_000_000_000:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        except ValueError:
            return None
    return None


def _employment_type(value: Any) -> EmploymentType:
    key = (_text(value) or "").casefold().replace("_", " ").replace("-", " ")
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


def _seniority(values: Any) -> Seniority:
    labels = _strings(values)
    if len(labels) != 1:
        return Seniority.UNKNOWN
    key = labels[0].casefold().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())
    mapping = {
        "intern": Seniority.INTERN,
        "entry level": Seniority.ENTRY_LEVEL,
        "junior": Seniority.JUNIOR,
        "mid": Seniority.MID,
        "mid level": Seniority.MID,
        "senior": Seniority.SENIOR,
        "lead": Seniority.LEAD,
        "manager": Seniority.MANAGER,
        "director": Seniority.DIRECTOR,
        "executive": Seniority.EXECUTIVE,
    }
    return mapping.get(key, Seniority.UNKNOWN)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) and number >= 0 else None


class HimalayasNormalizer:
    def normalize(self, raw_offer: RawOffer) -> JobOffer:
        if raw_offer.source_name != "Himalayas":
            raise NormalizationError("HimalayasNormalizer received an offer from another source")
        payload = raw_offer.payload
        title = _text(payload.get("title"))
        if title is None:
            raise NormalizationError("Himalayas job has no usable title")

        countries = _strings(payload.get("locationRestrictions"))
        timezones = _strings(payload.get("timezoneRestrictions"))
        minimum = _number(payload.get("minSalary"))
        maximum = _number(payload.get("maxSalary"))
        compensation = None
        if minimum is not None or maximum is not None:
            compensation = Compensation(components=[CompensationComponent(
                type=CompensationType.SALARY,
                min=minimum,
                max=maximum,
                currency=_text(payload.get("currency")),
                period=_text(payload.get("salaryPeriod")),
            )])

        try:
            return JobOffer(
                identity=OfferIdentity(sourceId=raw_offer.source_id),
                source=OfferSource(
                    name="Himalayas",
                    url=_url(raw_offer.provenance.get("source_url")),
                    retrievedAt=raw_offer.retrieved_at,
                ),
                position=Position(
                    title=title,
                    sourceSummary=_text(payload.get("excerpt")),
                    description=_description(payload.get("description")),
                    # Himalayas documents these as categories, not a reliably
                    # separated skills taxonomy; retain them as categories.
                    categories=_strings(payload.get("categories")) + _strings(payload.get("parentCategories")),
                ),
                company=Company(
                    name=_text(payload.get("companyName")),
                    logoUrl=_url(payload.get("companyLogo")),
                ),
                location=OfferLocation(
                    countries=countries,
                    locationRestrictions=countries,
                    timezoneRestrictions=timezones,
                    remote=True,
                    remoteScope=(RemoteScope.GLOBAL if not countries and not timezones
                                 else RemoteScope.COUNTRY if countries
                                 else RemoteScope.TIMEZONE if timezones
                                 else RemoteScope.UNKNOWN),
                ),
                employment=Employment(
                    type=_employment_type(payload.get("employmentType")),
                    seniority=_seniority(payload.get("seniority")),
                ),
                # Seniority labels are not a numeric experience range.
                experience=Experience(),
                compensation=compensation,
                dates=OfferDates(
                    publishedAt=_date(payload.get("pubDate")),
                    expiresAt=_date(payload.get("expiryDate")),
                ),
                application=Application(applyUrl=_url(payload.get("applicationLink"))),
            )
        except ValidationError as exc:
            raise NormalizationError("Himalayas job could not be represented by JobOffer") from exc
