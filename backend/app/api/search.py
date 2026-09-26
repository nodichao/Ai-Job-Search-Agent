from time import perf_counter

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.domain.job_offer import JobOffer
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
from app.services.search_criteria_builder import criteria_from_preferences

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    profile: UserProfile
    preferences: SearchPreferences


class SearchFromTextRequest(BaseModel):
    profile: UserProfile
    preferences_text: str = Field(min_length=1, max_length=20_000)


class SearchMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    sources: list[str]
    durationMs: int
    connectors: list[ConnectorAvailability]
    failed_sources: list[dict[str, str]] = Field(alias="failedSources")


class SearchResponse(BaseModel):
    results: list[JobOffer]
    meta: SearchMeta


def _runtime(request: Request) -> SearchRuntime:
    return request.app.state.search_runtime


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest, request: Request) -> SearchResponse:
    runtime = _runtime(request)
    criteria = criteria_from_preferences(body.preferences)
    started = perf_counter()
    pipeline_result = await runtime.pipeline.search(criteria)
    offers = pipeline_result.offers
    duration_ms = round((perf_counter() - started) * 1000)
    sources = list(dict.fromkeys(offer.source.name for offer in offers))
    return SearchResponse(
        results=offers,
        meta=SearchMeta(
            total=len(offers),
            sources=sources,
            durationMs=duration_ms,
            connectors=list(runtime.connectors),
            failed_sources=[
                {"source": failure.source_name, "category": failure.category}
                for failure in pipeline_result.failures
            ],
        ),
    )


@router.post("/from-text", response_model=SearchResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def search_from_text(_request: SearchFromTextRequest) -> None:
    raise HTTPException(status_code=501, detail="Preference parsing and job search are not implemented yet.")
