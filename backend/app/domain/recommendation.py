from pydantic import BaseModel, ConfigDict, Field


class Recommendation(BaseModel):
    """Shape only; decision and priority taxonomies remain intentionally open."""
    model_config = ConfigDict(extra="forbid")

    decision: str
    priority: str | None = None
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
