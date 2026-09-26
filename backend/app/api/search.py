from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    profile: UserProfile
    preferences: SearchPreferences


class SearchFromTextRequest(BaseModel):
    profile: UserProfile
    preferences_text: str = Field(min_length=1, max_length=20_000)


class SearchMeta(BaseModel):
    total: int
    sources: list[str]
    durationMs: int


class SearchResponse(BaseModel):
    results: list[dict[str, object]]
    meta: SearchMeta


@router.post("", response_model=SearchResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def search(_request: SearchRequest) -> None:
    raise HTTPException(status_code=501, detail="Job search is not implemented yet.")


@router.post("/from-text", response_model=SearchResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def search_from_text(_request: SearchFromTextRequest) -> None:
    raise HTTPException(status_code=501, detail="Preference parsing and job search are not implemented yet.")
