from datetime import datetime, timezone
from typing import Any, Protocol
from pydantic import BaseModel, ConfigDict, Field

from app.domain.search_criteria import SearchCriteria


class RawOffer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_name: str
    source_id: str | None = None
    payload: dict[str, Any]
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)


class JobSourceConnector(Protocol):
    source_name: str

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]: ...
