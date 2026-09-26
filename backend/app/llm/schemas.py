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


class MatchExplanation(BaseModel):
    explanation: str
