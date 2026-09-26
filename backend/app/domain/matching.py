from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class EvidenceStatus(StrEnum):
    SATISFIED = "SATISFIED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


class MatchDimension(BaseModel):
    name: str
    status: EvidenceStatus
    score: float | None = Field(default=None, ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class MatchingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=100, description="Relevance score, not hiring probability")
    confidence: float = Field(ge=0, le=1, description="Evidence completeness, independent of score")
    dimensions: list[MatchDimension] = Field(default_factory=list)
    matched_criteria: list[str] = Field(default_factory=list, alias="matchedCriteria")
    missing_criteria: list[str] = Field(default_factory=list, alias="missingCriteria")
    conflicts: list[str] = Field(default_factory=list)
