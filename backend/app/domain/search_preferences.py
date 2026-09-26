from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class PreferenceStrength(StrEnum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    OPTIONAL = "OPTIONAL"
    INFORMATIONAL = "INFORMATIONAL"


class SalaryPreference(BaseModel):
    minimum: float | None = Field(default=None, ge=0)
    maximum: float | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None


class SearchPreferences(BaseModel):
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
    # Importance is keyed by criterion so a hard constraint does not silently
    # make every other preference mandatory.
    preference_strength: dict[str, PreferenceStrength] = Field(default_factory=dict, alias="preferenceStrength")
