from app.domain.job_offer import JobOffer
from app.domain.matching import EvidenceStatus
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.services.matching_service import MatchingService


def offer(*, title="Platform Engineer", skills=None, minimum=5, remote=None):
    return JobOffer.model_validate({
        "identity": {"sourceId": "1"},
        "source": {"name": "Fixture"},
        "position": {"title": title, "skills": skills or []},
        "experience": {"minimumYears": minimum},
        "location": {"remote": remote},
    })


def test_full_match_uses_documented_weights_and_score_is_not_probability():
    result = MatchingService().match(
        UserProfile(skills=["Python"], jobTitles=["Platform Engineer"], totalExperienceYears=8),
        SearchPreferences(remote=True),
        offer(skills=["Python"], remote=True),
    )
    assert result.score == 100
    assert result.confidence == 1
    assert {item.name: item.weight for item in result.dimensions} == {
        "skills": 0.5, "preferences": 0.25, "experience": 0.15, "roleAlignment": 0.1,
    }
    assert all(item.status is EvidenceStatus.SATISFIED for item in result.dimensions)


def test_partial_skill_evidence_scores_coverage_without_calling_missing_skills_conflicts():
    result = MatchingService().match(
        UserProfile(skills=["Python"]), SearchPreferences(), offer(skills=["Python", "Go"])
    )
    skills = result.dimensions[0]
    assert skills.score == 50
    assert skills.status is EvidenceStatus.UNKNOWN
    assert result.conflicts == []
    assert any("go" in item.lower() for item in result.missing_criteria)


def test_disjoint_explicit_skill_lists_have_zero_overlap_but_no_claim_about_ability():
    result = MatchingService().match(
        UserProfile(skills=["Python"]), SearchPreferences(), offer(skills=["Go"])
    )
    assert result.dimensions[0].score == 0
    assert result.dimensions[0].status is EvidenceStatus.UNKNOWN
    assert result.conflicts == []


def test_experience_mismatch_is_explicit_conflict_with_partial_ratio():
    result = MatchingService().match(
        UserProfile(totalExperienceYears=2), SearchPreferences(), offer(minimum=5)
    )
    experience = next(item for item in result.dimensions if item.name == "experience")
    assert experience.status is EvidenceStatus.CONFLICT
    assert experience.score == 40
    assert result.conflicts


def test_unknown_dimensions_are_omitted_and_remaining_weights_are_renormalized():
    result = MatchingService().match(
        UserProfile(skills=["Python"]), SearchPreferences(remote=True),
        offer(skills=["Python"], remote=True, minimum=None),
    )
    assert result.score == 100
    assert result.confidence == 0.75
    assert sum(item.weight for item in result.dimensions) == 1
    assert next(item for item in result.dimensions if item.name == "experience").score is None


def test_missing_profile_and_offer_evidence_produces_no_arbitrary_zero_total():
    result = MatchingService().match(UserProfile(), SearchPreferences(), offer(skills=[], minimum=None))
    assert result.score is None
    assert result.confidence == 0
    assert all(item.score is None for item in result.dimensions)
    assert result.missing_criteria


def test_role_alignment_is_normalized_stable_and_conservative():
    service = MatchingService()
    profile = UserProfile(jobTitles=["Senior Platform Engineer"])
    job = offer(title="Platform Engineer")
    first = service.match(profile, SearchPreferences(), job)
    second = service.match(profile, SearchPreferences(), job)
    role = next(item for item in first.dimensions if item.name == "roleAlignment")
    assert role.score == 2 / 3 * 100
    assert first.model_dump() == second.model_dump()

    unrelated = service.match(UserProfile(jobTitles=["Accountant"]), SearchPreferences(), job)
    role = next(item for item in unrelated.dimensions if item.name == "roleAlignment")
    assert role.status is EvidenceStatus.UNKNOWN
    assert role.score == 0
