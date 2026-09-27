from app.domain.matching import FilteringResult, MatchingResult
from app.domain.recommendation import RecommendationDecision, RecommendationReasonCode
from app.services.recommendation_service import RecommendationPolicy, RecommendationService


def test_retained_strong_match_is_recommended_with_deterministic_reason():
    service = RecommendationService()
    result = service.recommend(FilteringResult(included=True), MatchingResult(score=80, confidence=0.75))
    assert result.decision is RecommendationDecision.RECOMMENDED
    assert [reason.code for reason in result.reasons] == [RecommendationReasonCode.SCORE_MEETS_THRESHOLD]
    assert result.reasons == service.recommend(FilteringResult(included=True), MatchingResult(score=80, confidence=0.75)).reasons
    assert "hiring" not in result.reasons[0].message.lower()


def test_low_score_is_not_recommended_and_threshold_is_configurable():
    below_default = RecommendationService().recommend(
        FilteringResult(included=True), MatchingResult(score=59, confidence=0.8)
    )
    assert below_default.decision is RecommendationDecision.NOT_RECOMMENDED

    service = RecommendationService(RecommendationPolicy(score_threshold=75, minimum_confidence=0.4))
    result = service.recommend(FilteringResult(included=True), MatchingResult(score=74.99, confidence=0.8))
    assert result.decision is RecommendationDecision.NOT_RECOMMENDED
    assert result.reasons[0].code is RecommendationReasonCode.SCORE_BELOW_THRESHOLD
    assert result.reasons[0].evidence == ["score=74.99", "threshold=75"]


def test_poc_thresholds_keep_score_and_confidence_as_independent_gates():
    service = RecommendationService(RecommendationPolicy(score_threshold=50, minimum_confidence=0.30))

    below_score = service.recommend(FilteringResult(included=True), MatchingResult(score=49.99, confidence=0.9))
    assert below_score.decision is RecommendationDecision.NOT_RECOMMENDED
    assert below_score.reasons[0].code is RecommendationReasonCode.SCORE_BELOW_THRESHOLD

    below_confidence = service.recommend(FilteringResult(included=True), MatchingResult(score=80, confidence=0.29))
    assert below_confidence.decision is RecommendationDecision.INSUFFICIENT_EVIDENCE
    assert below_confidence.reasons[0].code is RecommendationReasonCode.CONFIDENCE_TOO_LOW

    at_thresholds = service.recommend(FilteringResult(included=True), MatchingResult(score=50, confidence=0.30))
    assert at_thresholds.decision is RecommendationDecision.RECOMMENDED


def test_missing_score_and_low_confidence_are_insufficient_not_zero_score():
    service = RecommendationService()
    missing = service.recommend(FilteringResult(included=True), MatchingResult(score=None, confidence=0))
    assert missing.decision is RecommendationDecision.INSUFFICIENT_EVIDENCE
    assert missing.reasons[0].code is RecommendationReasonCode.SCORE_UNAVAILABLE
    low_confidence = service.recommend(FilteringResult(included=True), MatchingResult(score=99, confidence=0.49))
    assert low_confidence.decision is RecommendationDecision.INSUFFICIENT_EVIDENCE
    assert low_confidence.reasons[0].code is RecommendationReasonCode.CONFIDENCE_TOO_LOW


def test_excluded_offer_is_never_recommended_even_with_high_score():
    result = RecommendationService().recommend(
        FilteringResult(included=False, conflicts=["remote"]),
        MatchingResult(score=100, confidence=1),
    )
    assert result.decision is RecommendationDecision.NOT_RECOMMENDED
    assert result.reasons[0].code is RecommendationReasonCode.FILTERED_OUT
    assert result.reasons[0].evidence == ["remote"]


def test_unknown_matching_evidence_is_warned_about_not_promoted_to_conflict():
    result = RecommendationService().recommend(
        FilteringResult(included=True, unknownCriteria=["location"]),
        MatchingResult(score=80, confidence=0.75, missingCriteria=["experience: unavailable"]),
    )
    assert result.decision is RecommendationDecision.RECOMMENDED
    assert len(result.warnings) == 2
    assert "location" in result.warnings[0]
    assert result.reasons[0].code is RecommendationReasonCode.SCORE_MEETS_THRESHOLD


def test_invalid_policy_thresholds_are_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RecommendationPolicy(score_threshold=101)
