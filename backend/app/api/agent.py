"""Agentic workflow endpoint: CV + preferences in, orchestrated results out.

This route only translates HTTP <-> the agent orchestrator (`AgentService`).
It never calls the matching engine, the LLM, or the connectors directly, and
it never edits any score, filter decision, or recommendation the pipeline
produced.
"""
import json
from time import perf_counter

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.api.search import (
    ExcludedOfferView,
    OfferMatchView,
    SearchMeta,
    build_offer_views,
    build_search_meta,
)
from app.core.errors import LLMError
from app.domain.job_offer import JobOffer
from app.domain.recommendation import RankingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.llm.schemas import OfferExplanation
from app.services.agent_service import AgentService
from app.services.agent_tools import AgentToolError
from app.services.cv_document_extractor import MAX_CV_FILE_BYTES

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentStepView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool: str
    status: str
    detail: str | None = None


class ExplainedOfferView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    offer_id: str = Field(alias="offerId")
    source: str
    explanation: OfferExplanation


class AgentSearchResponse(BaseModel):
    status: str
    profile: UserProfile
    preferences: SearchPreferences
    results: list[JobOffer]
    matches: list[OfferMatchView]
    excluded: list[ExcludedOfferView]
    ranking: RankingResult
    explanations: list[ExplainedOfferView]
    meta: SearchMeta
    warnings: list[str] = Field(default_factory=list)
    steps: list[AgentStepView] = Field(default_factory=list)


def _agent_service(request: Request) -> AgentService:
    return request.app.state.agent_service


@router.post("/search", response_model=AgentSearchResponse)
async def agent_search(
    request: Request,
    file: UploadFile = File(...),
    preferences: str = Form(...),
) -> AgentSearchResponse:
    try:
        preferences_payload = json.loads(preferences)
    except ValueError:
        raise RequestValidationError([
            {"type": "json_invalid", "loc": ("body", "preferences"), "msg": "preferences must be valid JSON"},
        ]) from None
    try:
        prefs = SearchPreferences.model_validate(preferences_payload)
    except ValidationError as exc:
        raise RequestValidationError([
            {**item, "loc": ("body", "preferences", *item["loc"])} for item in exc.errors()
        ]) from exc

    if file.size is not None and file.size > MAX_CV_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded CV exceeds the 5 MiB limit")
    content = await file.read(MAX_CV_FILE_BYTES + 1)
    if len(content) > MAX_CV_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded CV exceeds the 5 MiB limit")

    started = perf_counter()
    try:
        run_result = await _agent_service(request).run(
            filename=file.filename or "",
            media_type=file.content_type,
            content=content,
            preferences=prefs,
        )
    except AgentToolError as exc:
        if exc.tool == "parse_cv":
            if isinstance(exc.__cause__, LLMError):
                raise HTTPException(status_code=502, detail="Profile extraction service is unavailable") from None
            raise HTTPException(status_code=422, detail=str(exc)) from None
        raise HTTPException(status_code=502, detail="Search pipeline is unavailable") from None
    duration_ms = round((perf_counter() - started) * 1000)

    runtime = request.app.state.search_runtime
    matches, excluded = build_offer_views(run_result.pipeline_result)
    return AgentSearchResponse(
        status="ok",
        profile=run_result.profile,
        preferences=run_result.preferences,
        results=run_result.pipeline_result.included_offers,
        matches=matches,
        excluded=excluded,
        ranking=run_result.pipeline_result.ranking,
        explanations=[
            ExplainedOfferView(offerId=item.offer_id, source=item.source, explanation=item.explanation)
            for item in run_result.explanations
        ],
        meta=build_search_meta(run_result.pipeline_result, runtime, duration_ms),
        warnings=run_result.warnings,
        steps=[
            AgentStepView(tool=step.tool, status=step.status, detail=step.detail)
            for step in run_result.steps
        ],
    )
