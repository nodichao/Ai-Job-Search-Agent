from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class OpenEnum(StrEnum):
    """Values named by the canonical model, with UNKNOWN retained explicitly."""
    pass


class EmploymentType(OpenEnum):
    UNKNOWN = "UNKNOWN"
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    FREELANCE = "FREELANCE"
    INTERNSHIP = "INTERNSHIP"
    TEMPORARY = "TEMPORARY"
    OTHER = "OTHER"


class Seniority(OpenEnum):
    UNKNOWN = "UNKNOWN"
    INTERN = "INTERN"
    ENTRY_LEVEL = "ENTRY_LEVEL"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    MANAGER = "MANAGER"
    DIRECTOR = "DIRECTOR"
    EXECUTIVE = "EXECUTIVE"


class RemoteScope(OpenEnum):
    UNKNOWN = "UNKNOWN"
    GLOBAL = "GLOBAL"
    REGION = "REGION"
    COUNTRY = "COUNTRY"
    TIMEZONE = "TIMEZONE"
    HYBRID = "HYBRID"


class ApplicationMethod(OpenEnum):
    UNKNOWN = "UNKNOWN"
    EXTERNAL_URL = "EXTERNAL_URL"
    EMAIL = "EMAIL"
    FORM = "FORM"


class LifecycleStatus(OpenEnum):
    UNKNOWN = "UNKNOWN"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class CompensationType(OpenEnum):
    UNKNOWN = "UNKNOWN"
    SALARY = "SALARY"
    HOURLY_RATE = "HOURLY_RATE"
    DAILY_RATE = "DAILY_RATE"
    COMMISSION = "COMMISSION"
    BONUS = "BONUS"
    EQUITY = "EQUITY"
    OTHER = "OTHER"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class OfferIdentity(DomainModel):
    id: str | None = None
    source_id: str | None = Field(default=None, alias="sourceId")
    slug: str | None = None
    offer_url: HttpUrl | None = Field(default=None, alias="offerUrl")


class OfferSource(DomainModel):
    name: str
    url: HttpUrl | None = None
    retrieved_at: datetime | None = Field(default=None, alias="retrievedAt")


class Position(DomainModel):
    title: str
    source_summary: str | None = Field(default=None, alias="sourceSummary")
    summary: str | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class Company(DomainModel):
    name: str | None = None
    id: str | None = None
    slug: str | None = None
    description: str | None = None
    logo_url: HttpUrl | None = Field(default=None, alias="logoUrl")
    website_url: HttpUrl | None = Field(default=None, alias="websiteUrl")
    location: str | None = None


class OfferLocation(DomainModel):
    locations: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    remote: bool | None = None
    remote_scope: RemoteScope = Field(default=RemoteScope.UNKNOWN, alias="remoteScope")
    location_restrictions: list[str] = Field(default_factory=list, alias="locationRestrictions")
    timezone_restrictions: list[str] = Field(default_factory=list, alias="timezoneRestrictions")


class Employment(DomainModel):
    type: EmploymentType = EmploymentType.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN
    department: str | None = None
    team: str | None = None
    schedule: str | None = None


class Experience(DomainModel):
    minimum_years: float | None = Field(default=None, ge=0, alias="minimumYears")
    maximum_years: float | None = Field(default=None, ge=0, alias="maximumYears")


class CompensationComponent(DomainModel):
    type: CompensationType = CompensationType.UNKNOWN
    amount: float | None = Field(default=None, ge=0)
    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None


class Compensation(DomainModel):
    components: list[CompensationComponent] = Field(default_factory=list)


class Languages(DomainModel):
    required: list[str] = Field(default_factory=list)
    preferred: list[str] = Field(default_factory=list)


class OfferDates(DomainModel):
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    application_deadline: datetime | None = Field(default=None, alias="applicationDeadline")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class Application(DomainModel):
    apply_url: HttpUrl | None = Field(default=None, alias="applyUrl")
    application_method: ApplicationMethod = Field(default=ApplicationMethod.UNKNOWN, alias="applicationMethod")
    instructions: str | None = None


class Lifecycle(DomainModel):
    status: LifecycleStatus = LifecycleStatus.UNKNOWN
    first_seen_at: datetime | None = Field(default=None, alias="firstSeenAt")
    last_seen_at: datetime | None = Field(default=None, alias="lastSeenAt")


class JobOffer(DomainModel):
    identity: OfferIdentity
    source: OfferSource
    position: Position
    company: Company = Field(default_factory=Company)
    location: OfferLocation = Field(default_factory=OfferLocation)
    employment: Employment = Field(default_factory=Employment)
    experience: Experience = Field(default_factory=Experience)
    compensation: Compensation | None = None
    languages: Languages = Field(default_factory=Languages)
    dates: OfferDates = Field(default_factory=OfferDates)
    application: Application = Field(default_factory=Application)
    lifecycle: Lifecycle = Field(default_factory=Lifecycle)
