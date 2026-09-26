"""Apply an explicit, configurable presentation policy to filter and match results."""
from pydantic import BaseModel, ConfigDict, Field

from app.domain.matching import FilteringResult, MatchingResult
from app.domain.recommendation import (
    Recommendation,
    RecommendationDecision,
    RecommendationReason,
    RecommendationReasonCode,
)


class RecommendationPolicy(BaseModel):
    """Thresholds are product policy, not learned or source-derived facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score_threshold: float = Field(default=60, ge=0, le=100)
    minimum_confidence: float = Field(default=0.5, ge=0, le=1)


class RecommendationService:
    def __init__(self, policy: RecommendationPolicy | None = None) -> None:
        self.policy = policy or RecommendationPolicy()

    def recommend(self, filtering: FilteringResult, matching: MatchingResult) -> Recommendation:
        warnings = []
        if filtering.unknown_criteria:
            warnings.append(
                "Some search criteria could not be verified: "
                + ", ".join(filtering.unknown_criteria)
            )
        if matching.missing_criteria:
            warnings.append("Some matching evidence is unknown; the decision uses available evidence only.")
        if matching.conflicts:
            warnings.append("Known mismatches are present; review the structured matching evidence.")

        if not filtering.included:
            return Recommendation(
                decision=RecommendationDecision.NOT_RECOMMENDED,
                reasons=[RecommendationReason(
                    code=RecommendationReasonCode.FILTERED_OUT,
                    message="Not presented because filtering found a conflict with a required search criterion.",
                    evidence=filtering.conflicts,
                )],
                warnings=warnings,
            )
        if matching.score is None:
            return Recommendation(
                decision=RecommendationDecision.INSUFFICIENT_EVIDENCE,
                reasons=[RecommendationReason(
                    code=RecommendationReasonCode.SCORE_UNAVAILABLE,
                    message="There is not enough structured evidence to calculate a relevance score.",
                    evidence=matching.missing_criteria,
                )],
                warnings=warnings,
            )
        if matching.confidence < self.policy.minimum_confidence:
            return Recommendation(
                decision=RecommendationDecision.INSUFFICIENT_EVIDENCE,
                reasons=[RecommendationReason(
                    code=RecommendationReasonCode.CONFIDENCE_TOO_LOW,
                    message="Available evidence is below the configured minimum for a presentation decision.",
                    evidence=[f"confidence={matching.confidence:g}",
                              f"minimumConfidence={self.policy.minimum_confidence:g}"],
                )],
                warnings=warnings,
            )
        if matching.score >= self.policy.score_threshold:
            return Recommendation(
                decision=RecommendationDecision.RECOMMENDED,
                reasons=[RecommendationReason(
                    code=RecommendationReasonCode.SCORE_MEETS_THRESHOLD,
                    message="The relevance score meets the configured presentation threshold.",
                    evidence=[f"score={matching.score:g}", f"threshold={self.policy.score_threshold:g}"],
                )],
                warnings=warnings,
            )
        return Recommendation(
            decision=RecommendationDecision.NOT_RECOMMENDED,
            reasons=[RecommendationReason(
                code=RecommendationReasonCode.SCORE_BELOW_THRESHOLD,
                message="The relevance score is below the configured presentation threshold.",
                evidence=[f"score={matching.score:g}", f"threshold={self.policy.score_threshold:g}"],
            )],
            warnings=warnings,
        )
