import pytest

from app.domain.job_offer import JobOffer
from app.domain.matching import EvidenceStatus
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import PreferenceStrength, SearchPreferences
from app.domain.user_profile import UserProfile
from app.services.filtering_service import FilteringService
from app.services.matching_service import MatchingService


def _offer(title: str) -> JobOffer:
    return JobOffer.model_validate({
        "identity": {"sourceId": "title-test"},
        "source": {"name": "Fixture"},
        "position": {"title": title},
    })


@pytest.mark.parametrize(
    ("requested", "actual", "expected"),
    [
        ("Full-Stack Developer", "DESARROLLADOR FULL STACK", EvidenceStatus.UNKNOWN),
        ("Full-Stack Developer", "Frontend Developer", EvidenceStatus.UNKNOWN),
        ("Full-Stack Developer", "Accountant", EvidenceStatus.CONFLICT),
        ("Full-Stack Developer", "Full Stack Developer", EvidenceStatus.SATISFIED),
        ("Full-Stack Developer", "", EvidenceStatus.UNKNOWN),
    ],
)
def test_filtering_and_matching_share_conservative_title_assessment(requested, actual, expected):
    strength = PreferenceStrength.REQUIRED if expected is EvidenceStatus.CONFLICT else PreferenceStrength.PREFERRED
    offer = _offer(actual)

    filtering = FilteringService().evaluate(
        SearchCriteria(jobTitles=[requested]), offer, {"jobTitles": strength}
    )
    matching = MatchingService().match(
        UserProfile(jobTitles=[requested]),
        SearchPreferences(jobTitles=[requested], preferenceStrength={"jobTitles": strength}),
        offer,
    )
    preference_dimension = next(d for d in matching.dimensions if d.name == "preferences")
    role_dimension = next(d for d in matching.dimensions if d.name == "roleAlignment")

    assessment = next(item for item in filtering.criteria if item.name == "jobTitles")
    assert assessment.status is expected
    assert preference_dimension.status is expected
    assert filtering.included is (expected is not EvidenceStatus.CONFLICT or strength is not PreferenceStrength.REQUIRED)
    if expected is EvidenceStatus.SATISFIED:
        assert role_dimension.status is EvidenceStatus.SATISFIED
    elif expected is EvidenceStatus.UNKNOWN:
        assert role_dimension.status is EvidenceStatus.UNKNOWN
    if expected is EvidenceStatus.CONFLICT and strength is PreferenceStrength.REQUIRED:
        assert not filtering.included


def test_preferred_partial_title_is_retained_but_never_reported_as_satisfied():
    offer = _offer("DESARROLLADOR FULL STACK")
    filtering = FilteringService().evaluate(
        SearchCriteria(jobTitles=["Full-Stack Developer"]), offer,
        {"jobTitles": PreferenceStrength.PREFERRED},
    )
    matching = MatchingService().match(
        UserProfile(jobTitles=["Full-Stack Developer"]),
        SearchPreferences(jobTitles=["Full-Stack Developer"]), offer,
    )
    assert filtering.included
    assert filtering.unknown_criteria == ["jobTitles"]
    assert filtering.satisfied_criteria == []
    assert next(d for d in matching.dimensions if d.name == "preferences").status is EvidenceStatus.UNKNOWN
    assert next(d for d in matching.dimensions if d.name == "roleAlignment").status is EvidenceStatus.UNKNOWN
