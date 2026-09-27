from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.search_preferences import PreferenceStrength, SalaryPreference


class ExtractedProfile(BaseModel):
    """LLM output fields; source metadata is set by the application, not guessed."""

    model_config = ConfigDict(extra="forbid")

    skills: list[str] = Field(default_factory=list)
    job_titles: list[str] = Field(default_factory=list, alias="jobTitles")
    experience: list[str] = Field(default_factory=list)
    total_experience_years: float | None = Field(default=None, ge=0, alias="totalExperienceYears")
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)


class ProfileExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: ExtractedProfile


class PreferenceExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferences: ExtractedPreferences


class ExtractedPreferenceStrengths(BaseModel):
    """Known preference keys only, represented without arbitrary JSON keys."""

    model_config = ConfigDict(extra="forbid")

    job_titles: PreferenceStrength | None = Field(default=None, alias="jobTitles")
    locations: PreferenceStrength | None = None
    countries: PreferenceStrength | None = None
    remote: PreferenceStrength | None = None
    seniority: PreferenceStrength | None = None
    employment_types: PreferenceStrength | None = Field(default=None, alias="employmentTypes")
    skills: PreferenceStrength | None = None
    salary: PreferenceStrength | None = None
    companies: PreferenceStrength | None = None
    timezone: PreferenceStrength | None = None


class ExtractedPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_titles: list[str] = Field(default_factory=list, alias="jobTitles")
    locations: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    remote: bool | None = None
    seniority: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list, alias="employmentTypes")
    skills: list[str] = Field(default_factory=list)
    salary: SalaryPreference | None = None
    companies: list[str] = Field(default_factory=list)
    timezone: str | None = None
    preference_strength: ExtractedPreferenceStrengths = Field(
        default_factory=ExtractedPreferenceStrengths, alias="preferenceStrength"
    )


class OfferExplanation(BaseModel):
    """One offer's LLM-generated narrative, grounded in supplied match evidence only.

    The LLM never computes or restates a score/rank/decision here; those stay
    the deterministic engine's exclusive output. `recommendation_context`
    explains the engine's own decision in plain language -- it must not
    contradict it.
    """

    model_config = ConfigDict(extra="forbid")

    offer_id: str = Field(alias="offerId")
    summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    recommendation_context: str = Field(alias="recommendationContext")
    next_steps: list[str] = Field(default_factory=list, alias="nextSteps")


class MatchExplanationBatch(BaseModel):
    """Structured output for explaining several offers in a single LLM call."""

    model_config = ConfigDict(extra="forbid")

    explanations: list[OfferExplanation] = Field(default_factory=list)


class ExplainableCandidate(BaseModel):
    """Compact, already-extracted candidate facts -- never the raw CV text."""

    job_titles: list[str] = Field(default_factory=list, alias="jobTitles")
    skills: list[str] = Field(default_factory=list)
    total_experience_years: float | None = Field(default=None, alias="totalExperienceYears")
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class ExplainableOfferFacts(BaseModel):
    """Compact, source-supported offer facts; unavailable fields stay null/empty."""

    title: str
    company: str | None = None
    locations: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    remote: bool | None = None
    remote_scope: str | None = Field(default=None, alias="remoteScope")
    employment_type: str | None = Field(default=None, alias="employmentType")
    seniority: str | None = None


class ExplainableDimension(BaseModel):
    name: str
    status: str
    score: float | None = None
    evidence: list[str] = Field(default_factory=list)


class ExplainableMatch(BaseModel):
    """Everything `explain_match` may use for one offer -- all of it already
    computed deterministically by the engine. The LLM must not be asked to
    (and cannot, from this alone) recompute score/confidence/decision."""

    offer_id: str = Field(alias="offerId")
    offer: ExplainableOfferFacts
    candidate: ExplainableCandidate
    score: float | None = None
    confidence: float
    decision: str
    decision_reasons: list[str] = Field(default_factory=list, alias="decisionReasons")
    satisfied_criteria: list[str] = Field(default_factory=list, alias="satisfiedCriteria")
    unknown_criteria: list[str] = Field(default_factory=list, alias="unknownCriteria")
    conflicts: list[str] = Field(default_factory=list)
    dimensions: list[ExplainableDimension] = Field(default_factory=list)
