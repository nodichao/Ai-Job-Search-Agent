import pytest
from pydantic import ValidationError

from app.domain.job_offer import JobOffer, RemoteScope
from app.domain.matching import EvidenceStatus, MatchingResult
from app.domain.search_preferences import PreferenceStrength, SearchPreferences
from app.domain.user_profile import UserProfile


def test_profile_and_preferences_contracts() -> None:
    profile = UserProfile.model_validate({"skills": ["Python"], "totalExperienceYears": 4})
    prefs = SearchPreferences.model_validate({"remote": None, "preferenceStrength": {"remote": "REQUIRED"}})
    assert profile.total_experience_years == 4
    assert prefs.preference_strength["remote"] is PreferenceStrength.REQUIRED


def test_job_offer_keeps_semantically_distinct_fields() -> None:
    offer = JobOffer.model_validate({
        "identity": {"sourceId": "42", "offerUrl": "https://jobs.example/42"},
        "source": {"name": "Example", "url": "https://jobs.example"},
        "position": {"title": "Engineer", "sourceSummary": "Source text", "summary": "Derived text"},
        "location": {"remote": True},
        "dates": {"publishedAt": "2026-01-01T00:00:00Z", "applicationDeadline": "2026-02-01T00:00:00Z"},
        "application": {"applyUrl": "https://apply.example/42"},
    })
    assert offer.identity.offer_url != offer.application.apply_url
    assert offer.position.source_summary != offer.position.summary
    assert offer.dates.application_deadline is not None and offer.dates.expires_at is None
    assert offer.location.remote is True and offer.location.remote_scope is RemoteScope.UNKNOWN


def test_offer_requires_identity_source_and_title() -> None:
    with pytest.raises(ValidationError):
        JobOffer.model_validate({})


def test_unknown_is_distinct_from_conflict_and_score_from_confidence() -> None:
    result = MatchingResult(score=90, confidence=0.4, dimensions=[{"name": "location", "status": "UNKNOWN"}])
    assert result.dimensions[0].status is EvidenceStatus.UNKNOWN
    assert result.score != result.confidence


def test_profile_rejects_negative_experience() -> None:
    with pytest.raises(ValidationError):
        UserProfile(totalExperienceYears=-1)
