from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.job_offer import JobOffer
from app.domain.matching import FilteringResult, MatchingResult


class RecommendationDecision(StrEnum):
    RECOMMENDED = "RECOMMENDED"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RecommendationReasonCode(StrEnum):
    FILTERED_OUT = "FILTERED_OUT"
    SCORE_UNAVAILABLE = "SCORE_UNAVAILABLE"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    SCORE_MEETS_THRESHOLD = "SCORE_MEETS_THRESHOLD"
    SCORE_BELOW_THRESHOLD = "SCORE_BELOW_THRESHOLD"


class RecommendationReason(BaseModel):
    code: RecommendationReasonCode
    message: str
    evidence: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """A presentation decision, separate from canonical job offer facts."""

    model_config = ConfigDict(extra="forbid")

    decision: RecommendationDecision
    priority: str | None = None
    reasons: list[RecommendationReason] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RecommendationCandidate(BaseModel):
    """The offer and deterministic result required by the ranking stage."""

    offer: JobOffer
    filtering: FilteringResult
    recommendation: Recommendation
    matching: MatchingResult


class RankedOffer(BaseModel):
    rank: int = Field(ge=1)
    offer: JobOffer
    recommendation: Recommendation
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class RankingResult(BaseModel):
    offers: list[RankedOffer] = Field(default_factory=list)
    total: int = Field(ge=0)
