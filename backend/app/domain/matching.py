from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field

from app.domain.search_preferences import PreferenceStrength


class EvidenceStatus(StrEnum):
    SATISFIED = "SATISFIED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


class MatchDimension(BaseModel):
    name: str
    status: EvidenceStatus
    score: float | None = Field(default=None, ge=0, le=100)
    weight: float = Field(default=0, ge=0, le=1, description="Effective share of the evaluated score")
    evidence: list[str] = Field(default_factory=list)
    matched_criteria: list[str] = Field(default_factory=list, alias="matchedCriteria")
    missing_criteria: list[str] = Field(default_factory=list, alias="missingCriteria")
    conflicts: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class MatchingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    score: float | None = Field(default=None, ge=0, le=100, description="Relevance score, not hiring probability; null when no dimension can be evaluated")
    confidence: float = Field(ge=0, le=1, description="Evidence completeness, independent of score")
    dimensions: list[MatchDimension] = Field(default_factory=list)
    matched_criteria: list[str] = Field(default_factory=list, alias="matchedCriteria")
    missing_criteria: list[str] = Field(default_factory=list, alias="missingCriteria")
    conflicts: list[str] = Field(default_factory=list)


class CriterionAssessment(BaseModel):
    name: str
    strength: PreferenceStrength
    status: EvidenceStatus
    evidence: list[str] = Field(default_factory=list)


class FilteringResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    included: bool
    criteria: list[CriterionAssessment] = Field(default_factory=list)
    satisfied_criteria: list[str] = Field(default_factory=list, alias="satisfiedCriteria")
    unknown_criteria: list[str] = Field(default_factory=list, alias="unknownCriteria")
    conflicts: list[str] = Field(default_factory=list)


class MatchExplanation(BaseModel):
    """Deterministic presentation of structured filtering and matching evidence."""

    model_config = ConfigDict(populate_by_name=True)

    score: float | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    dimensions: list[MatchDimension] = Field(default_factory=list)
    satisfied_criteria: list[str] = Field(default_factory=list, alias="satisfiedCriteria")
    unknown_criteria: list[str] = Field(default_factory=list, alias="unknownCriteria")
    conflicts: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
