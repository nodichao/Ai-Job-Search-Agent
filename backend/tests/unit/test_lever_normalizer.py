import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.connectors.base import RawOffer
from app.connectors.lever import LeverNormalizer
from app.core.errors import NormalizationError
from app.domain.job_offer import EmploymentType

FIXTURE = Path(__file__).parents[1] / "fixtures" / "lever" / "page_one.json"


def raw(payload, source_id="lever-101", company="Example"):
    return RawOffer(source_name="Lever", source_id=source_id, payload=payload,
                    retrieved_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                    provenance={"company_name": company})


def test_maps_documented_fields_and_keeps_urls_and_dates_distinct():
    item = json.loads(FIXTURE.read_text(encoding="utf-8"))[0]
    offer = LeverNormalizer().normalize(raw(item))
    assert offer.identity.source_id == "lever-101"
    assert offer.position.title == "Platform Engineer"
    assert offer.company.name == "Example"
    assert offer.location.locations == ["Dakar, Senegal", "Remote - Senegal"]
    assert offer.location.remote is None
    assert offer.employment.type == EmploymentType.FULL_TIME
    assert offer.employment.team == "Infrastructure"
    assert offer.employment.department == "Engineering"
    assert offer.source.url is not None
    assert offer.identity.offer_url is None
    assert offer.application.apply_url is None
    assert offer.dates.published_at is offer.dates.updated_at is offer.dates.application_deadline is offer.dates.expires_at is None
    assert offer.position.summary is None


def test_missing_and_unexpected_data_stay_unknown():
    offer = LeverNormalizer().normalize(raw({"id": "x", "text": "Analyst", "unexpected": "ignored"}, company=None))
    assert offer.company.name is None
    assert offer.location.locations == []
    assert offer.location.remote is None
    assert offer.employment.type == EmploymentType.UNKNOWN
    assert offer.position.description is None
    assert offer.compensation is None
    assert offer.identity.offer_url is None
    assert "unexpected" not in offer.model_dump(mode="json")


def test_missing_required_title_is_a_normalization_error():
    with pytest.raises(NormalizationError):
        LeverNormalizer().normalize(raw({"id": "x"}))
