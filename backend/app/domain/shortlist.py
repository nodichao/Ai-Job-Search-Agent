from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.job_offer import JobOffer


class ShortlistStatus(StrEnum):
    SAVED = "SAVED"
    INTERESTED = "INTERESTED"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ShortlistEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    offer: JobOffer
    status: ShortlistStatus = ShortlistStatus.SAVED
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ShortlistStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ShortlistStatus
