from app.domain.matching import EvidenceStatus, FilteringResult, MatchDimension, MatchingResult
from app.services.explanation_service import ExplanationService


def test_explanation_uses_filtering_and_matching_evidence_without_recalculating():
    filtering = FilteringResult(
        included=True,
        satisfiedCriteria=["remote"],
        unknownCriteria=["salary"],
        conflicts=[],
    )
    matching = MatchingResult(
        score=72.5,
        confidence=0.75,
        dimensions=[MatchDimension(name="skills", status=EvidenceStatus.UNKNOWN, score=50, weight=1,
                                   evidence=["Not evidenced in profile: Go"])],
        missingCriteria=["skills: Not evidenced in profile: Go"],
    )
    explanation = ExplanationService().explain(filtering, matching)
    assert explanation.score == matching.score
    assert explanation.confidence == matching.confidence
    assert "remote" in explanation.satisfied_criteria
    assert "salary" in explanation.unknown_criteria
    assert explanation.conflicts == []
    assert any("not a hiring probability" in reason.lower() for reason in explanation.reasons)
