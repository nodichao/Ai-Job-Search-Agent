from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skills: list[str] = Field(default_factory=list)
    job_titles: list[str] = Field(default_factory=list, alias="jobTitles")
    experience: list[str] = Field(default_factory=list)
    total_experience_years: float | None = Field(default=None, ge=0, alias="totalExperienceYears")
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    raw_source_metadata: dict[str, object] = Field(default_factory=dict, alias="rawSourceMetadata")
