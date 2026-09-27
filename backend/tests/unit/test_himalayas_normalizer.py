from datetime import datetime, timezone

import pytest

from app.connectors.base import RawOffer
from app.connectors.himalayas import HimalayasNormalizer
from app.core.errors import NormalizationError
from app.domain.job_offer import EmploymentType, RemoteScope, Seniority


@pytest.fixture
def raw():
    return RawOffer(
        source_name="Himalayas", source_id="h-123",
        retrieved_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        provenance={"source_url": "https://himalayas.app/"},
        payload={
            "title": "Senior Platform Engineer", "excerpt": "Source excerpt",
            "description": "<p>Build systems</p><script>ignore()</script>",
            "companyName": "Example Co", "companyLogo": "https://example.com/logo.png",
            "employmentType": "Full-time", "seniority": ["senior"],
            "locationRestrictions": ["US", "CA"], "timezoneRestrictions": ["UTC-8"],
            "categories": ["Engineering"], "parentCategories": ["Technology"],
            "minSalary": 120000, "maxSalary": 160000, "currency": "USD",
            "salaryPeriod": "year", "pubDate": 1780000000000,
            "expiryDate": "2026-12-31T00:00:00Z",
            "applicationLink": "https://example.com/apply/123",
            "unexpected": "must not appear in canonical model",
        },
    )


def test_normalizes_documented_fields_without_conflating_urls_or_summaries(raw):
    offer = HimalayasNormalizer().normalize(raw)
    assert offer.identity.source_id == "h-123"
    assert offer.identity.offer_url is None
    assert str(offer.application.apply_url) == "https://example.com/apply/123"
    assert str(offer.source.url) == "https://himalayas.app/"
    assert offer.position.title == "Senior Platform Engineer"
    assert offer.position.source_summary == "Source excerpt"
    assert offer.position.summary is None
    assert offer.position.description == "Build systems"
    assert offer.company.name == "Example Co"
    assert str(offer.company.logo_url) == "https://example.com/logo.png"
    assert offer.location.remote is True
    assert offer.location.remote_scope == RemoteScope.COUNTRY
    assert offer.location.countries == ["US", "CA"]
    assert offer.employment.type == EmploymentType.FULL_TIME
    assert offer.employment.seniority == Seniority.SENIOR
    assert offer.experience.minimum_years is None
    assert offer.position.skills == []
    assert offer.position.categories == ["Engineering", "Technology"]
    component = offer.compensation.components[0]
    assert (component.min, component.max, component.currency, component.period) == (120000, 160000, "USD", "year")
    assert offer.dates.published_at is not None
    assert offer.dates.published_at.year == 2026
    assert offer.dates.expires_at is not None
    assert offer.dates.updated_at is None
    assert offer.dates.application_deadline is None
    assert "unexpected" not in offer.model_dump()


@pytest.mark.parametrize("payload", [
    {"title": "Software Engineer"},
    {"title": "Analyst", "companyName": ""},
    {"title": "Analyst", "minSalary": "unknown", "locationRestrictions": None},
    {"title": "Analyst", "seniority": ["senior", "lead"], "categories": None},
    {"title": "Analyst", "description": "", "applicationLink": None, "pubDate": "not-a-date"},
])
def test_missing_and_unexpected_values_remain_unknown_or_empty(payload):
    offer = HimalayasNormalizer().normalize(RawOffer(source_name="Himalayas", payload=payload))
    assert offer.experience.minimum_years is None
    assert offer.position.skills == []
    assert offer.location.countries == []
    assert offer.location.remote_scope == RemoteScope.GLOBAL
    assert offer.compensation is None
    assert offer.employment.seniority == Seniority.UNKNOWN
    assert offer.position.description is None
    assert offer.application.apply_url is None
    assert offer.dates.published_at is None


def test_missing_title_rejected_and_wrong_source_rejected():
    normalizer = HimalayasNormalizer()
    with pytest.raises(NormalizationError):
        normalizer.normalize(RawOffer(source_name="Himalayas", payload={}))
    with pytest.raises(NormalizationError):
        normalizer.normalize(RawOffer(source_name="RemoteOK", payload={"title": "x"}))


def test_himalayas_publication_epoch_seconds_and_milliseconds_are_supported():
    normalizer = HimalayasNormalizer()
    seconds = normalizer.normalize(RawOffer(
        source_name="Himalayas", payload={"title": "A", "pubDate": 1780000000}
    ))
    milliseconds = normalizer.normalize(RawOffer(
        source_name="Himalayas", payload={"title": "A", "pubDate": 1780000000000}
    ))
    assert seconds.dates.published_at == milliseconds.dates.published_at
    assert seconds.dates.published_at.year == 2026
