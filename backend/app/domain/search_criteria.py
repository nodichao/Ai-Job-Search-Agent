from pydantic import BaseModel, ConfigDict, Field

from app.domain.search_preferences import SalaryPreference


class SearchCriteria(BaseModel):
    """Source-independent search intent; connector capabilities are separate."""
    model_config = ConfigDict(extra="forbid")

    keywords: list[str] = Field(default_factory=list)
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
    departments: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
