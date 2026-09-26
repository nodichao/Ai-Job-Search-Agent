from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.connectors.base import RawOffer
from app.connectors.remoteok.normalizer import RemoteOKNormalizer
from app.core.errors import NormalizationError
from app.domain.job_offer import CompensationType, RemoteScope
from app.domain.matching import EvidenceStatus

FIXTURES = Path(__file__).parents[1] / "fixtures" / "remoteok"


def _raw(name: str = "offer_list.json") -> RawOffer:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))[0]
    return RawOffer(
        source_name="RemoteOK",
        source_id=str(payload["id"]) if "id" in payload else None,
        payload=payload,
        retrieved_at=datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc),
        provenance={"source_url": "https://remoteok.example.invalid/", "attribution_required": True},
    )


def test_normalizer_maps_documented_fields_and_keeps_urls_and_dates_distinct() -> None:
    raw = _raw()
    offer = RemoteOKNormalizer().normalize(raw)

    assert offer.identity.source_id == "735421"
    assert offer.identity.slug == "senior-platform-engineer-exampleco"
    assert str(offer.identity.offer_url) == "https://remoteok.example.invalid/remote-jobs/735421"
    assert str(offer.source.url) == "https://remoteok.example.invalid/"
    assert str(offer.application.apply_url) == "https://apply.example.invalid/jobs/735421"
    assert len({str(offer.source.url), str(offer.identity.offer_url), str(offer.application.apply_url)}) == 3
    assert offer.source.retrieved_at == raw.retrieved_at

    assert offer.position.title == "Senior Platform Engineer"
    assert offer.position.description == raw.payload["description"]
    assert offer.position.source_summary is None
    assert offer.position.summary is None
    assert offer.position.skills == []
    assert offer.position.categories == ["python", "platform", "distributed-systems"]
    assert offer.company.name == "ExampleCo"
    assert str(offer.company.logo_url) == "https://cdn.example.invalid/exampleco.png"
    assert offer.company.website_url is None
    assert offer.location.locations == ["Europe or Africa"]
    assert offer.location.remote is None
    assert offer.location.remote_scope is RemoteScope.UNKNOWN

    component = offer.compensation.components[0]
    assert component.min == 85000
    assert component.max == 115000
    assert component.type is CompensationType.UNKNOWN
    assert component.currency is None
    assert component.period is None
    assert offer.dates.published_at == datetime(2026, 9, 18, 9, 30, tzinfo=timezone.utc)
    assert offer.dates.updated_at is None
    assert offer.dates.application_deadline is None
    assert offer.dates.expires_at is None
    assert offer.lifecycle.first_seen_at is None
    assert offer.lifecycle.last_seen_at is None


def test_normalizer_preserves_unknowns_and_tolerates_partial_or_unexpected_data() -> None:
    raw = _raw("partial_offer_list.json")
    offer = RemoteOKNormalizer().normalize(raw)

    assert offer.identity.source_id is None
    assert offer.identity.offer_url is None
    assert offer.company.name is None
    assert offer.company.logo_url is None
    assert offer.company.website_url is None
    assert offer.location.locations == []
    assert offer.location.remote is None
    assert offer.location.remote_scope is RemoteScope.UNKNOWN
    assert offer.position.description is None
    assert offer.position.categories == ["operations"]
    assert offer.position.summary is None and offer.position.source_summary is None
    assert offer.application.apply_url is None
    assert offer.compensation is None
    assert offer.dates.published_at is None
    assert EvidenceStatus.UNKNOWN is not EvidenceStatus.CONFLICT


def test_normalizer_keeps_single_salary_bound_without_inventing_the_other() -> None:
    raw = _raw()
    raw.payload["salary_max"] = None
    offer = RemoteOKNormalizer().normalize(raw)
    component = offer.compensation.components[0]
    assert component.min == 85000
    assert component.max is None
    assert component.type is CompensationType.UNKNOWN


def test_normalizer_rejects_wrong_source_or_missing_title() -> None:
    normalizer = RemoteOKNormalizer()
    raw = _raw()
    raw.source_name = "Other"
    with pytest.raises(NormalizationError):
        normalizer.normalize(raw)

    raw = _raw()
    raw.payload.pop("position")
    with pytest.raises(NormalizationError, match="position/title"):
        normalizer.normalize(raw)


def test_raw_source_fields_do_not_leak_into_canonical_offer() -> None:
    offer = RemoteOKNormalizer().normalize(_raw())
    serialized = json.dumps(offer.model_dump(mode="json", by_alias=True))
    assert "company_logo" not in serialized
    assert "salary_min" not in serialized
    assert "apply_url" not in serialized
    assert "unmapped_source_field" not in serialized
