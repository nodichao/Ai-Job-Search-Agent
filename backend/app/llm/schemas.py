from pydantic import BaseModel, ConfigDict, Field

from app.domain.search_preferences import SearchPreferences


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
    preferences: SearchPreferences


class MatchExplanation(BaseModel):
    explanation: str
