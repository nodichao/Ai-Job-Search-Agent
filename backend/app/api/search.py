from time import perf_counter

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.domain.job_offer import JobOffer, OfferIdentity
from app.domain.matching import FilteringResult, MatchExplanation, MatchingResult
from app.domain.recommendation import RankingResult, Recommendation
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


class NormalizationFailureBySource(BaseModel):
    source: str
    rejected: int


class NormalizationFailureSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_rejected: int = Field(alias="totalRejected")
    by_source: list[NormalizationFailureBySource] = Field(alias="bySource")


class SearchMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    sources: list[str]
    durationMs: int
    connectors: list[ConnectorAvailability]
    failed_sources: list[dict[str, str]] = Field(alias="failedSources")
    normalization_failures: NormalizationFailureSummary = Field(
        default_factory=lambda: NormalizationFailureSummary(totalRejected=0, bySource=[]),
        alias="normalizationFailures",
    )


class OfferMatchView(BaseModel):
    offer_identity: OfferIdentity = Field(alias="offerIdentity")
    filtering: FilteringResult
    matching: MatchingResult
    explanation: MatchExplanation
    recommendation: Recommendation


class ExcludedOfferView(BaseModel):
    offer: JobOffer
    filtering: FilteringResult
    matching: MatchingResult
    explanation: MatchExplanation
    recommendation: Recommendation


class SearchResponse(BaseModel):
    results: list[JobOffer]
    matches: list[OfferMatchView]
    excluded: list[ExcludedOfferView]
    ranking: RankingResult
    meta: SearchMeta


def _runtime(request: Request) -> SearchRuntime:
    return request.app.state.search_runtime


async def _search_response(
    request: Request,
    profile: UserProfile,
    preferences: SearchPreferences,
) -> SearchResponse:
    runtime = _runtime(request)
    criteria = criteria_from_preferences(preferences)
    started = perf_counter()
    pipeline_result = await runtime.pipeline.search(criteria, profile, preferences)
    offers = pipeline_result.included_offers
    duration_ms = round((perf_counter() - started) * 1000)
    sources = list(dict.fromkeys(offer.source.name for offer in offers))
    return SearchResponse(
        results=offers,
        matches=[
            OfferMatchView(
                offerIdentity=item.offer.identity,
                filtering=item.filtering,
                matching=item.matching,
                explanation=item.explanation,
                recommendation=item.recommendation,
            )
            for item in pipeline_result.analyses if item.filtering.included
        ],
        excluded=[
            ExcludedOfferView(
                offer=item.offer,
                filtering=item.filtering,
                matching=item.matching,
                explanation=item.explanation,
                recommendation=item.recommendation,
            )
            for item in pipeline_result.analyses if not item.filtering.included
        ],
        ranking=pipeline_result.ranking,
        meta=SearchMeta(
            total=len(offers),
            sources=sources,
            durationMs=duration_ms,
            connectors=list(runtime.connectors),
            failed_sources=[
                {"source": failure.source_name, "category": failure.category}
                for failure in pipeline_result.failures
            ],
            normalization_failures=NormalizationFailureSummary(
                totalRejected=sum(pipeline_result.normalization_rejected_by_source.values()),
                bySource=[
                    NormalizationFailureBySource(source=source, rejected=count)
                    for source, count in pipeline_result.normalization_rejected_by_source.items()
                ],
            ),
        ),
    )


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest, request: Request) -> SearchResponse:
    return await _search_response(request, body.profile, body.preferences)


@router.post("/from-text", response_model=SearchResponse)
async def search_from_text(body: SearchFromTextRequest, request: Request) -> SearchResponse:
    if not body.preferences_text.strip():
        raise HTTPException(status_code=422, detail="preferences_text must not be empty")
    try:
        parsed = await request.app.state.llm_service.parse_preferences(body.preferences_text)
        preferences = SearchPreferences.model_validate(parsed)
    except Exception:
        raise HTTPException(status_code=502, detail="Preference parsing service is unavailable") from None
    return await _search_response(request, body.profile, preferences)
