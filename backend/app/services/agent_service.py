"""Sequential, bounded orchestration of the three agent tools.

The workflow has exactly one valid order -- parse_cv, then search_jobs, then
explain_match -- because each step consumes the previous step's real output
(the extracted profile; the pipeline's real results). There is no ordering
decision left for an LLM to make, so this is an explicit, deterministic
orchestrator rather than a native LLM tool-calling loop: it is the bounded
fallback the project's own spec allows when tool-calling would add
reliability risk without adding real flexibility. Each of the three tools is
invoked at most once per run; there is no loop, no dynamic dispatch, and no
tool name or argument the LLM can choose -- only the three fixed calls below.

This service never computes or edits a score, filter decision, confidence, or
recommendation. Those remain the exclusive, unmodified output of
`SearchPipeline` (collection -> normalization -> deduplication -> filtering ->
matching -> recommendation -> ranking).
"""
import logging
from dataclasses import dataclass, field

from app.core.errors import LLMError
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.llm.base import LLMService
from app.services.agent_tools import (
    AgentToolError,
    ExplainedOffer,
    explain_match_tool,
    parse_cv_tool,
    search_jobs_tool,
)
from app.services.cv_document_extractor import CvDocumentError
from app.services.profile_service import ProfileService
from app.services.search_pipeline import SearchPipeline, SearchPipelineResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentStep:
    tool: str
    status: str  # "success" | "fallback" | "error"
    detail: str | None = None


@dataclass(frozen=True)
class AgentRunResult:
    profile: UserProfile
    preferences: SearchPreferences
    pipeline_result: SearchPipelineResult
    explanations: list[ExplainedOffer] = field(default_factory=list)
    steps: list[AgentStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class AgentService:
    def __init__(
        self,
        profile_service: ProfileService,
        search_pipeline: SearchPipeline,
        llm_service: LLMService,
        *,
        max_explanations: int = 5,
    ) -> None:
        self._profile_service = profile_service
        self._search_pipeline = search_pipeline
        self._llm_service = llm_service
        self._max_explanations = max_explanations

    async def run(
        self,
        *,
        filename: str,
        media_type: str | None,
        content: bytes,
        preferences: SearchPreferences,
        max_explanations: int | None = None,
    ) -> AgentRunResult:
        steps: list[AgentStep] = []

        # Step 1: parse_cv -- a failure here must stop the run; nothing
        # downstream can proceed without a real extracted profile.
        try:
            profile = await parse_cv_tool(
                self._profile_service, filename=filename, media_type=media_type, content=content,
            )
        except CvDocumentError as exc:
            steps.append(AgentStep(tool="parse_cv", status="error", detail=str(exc)))
            raise AgentToolError("parse_cv", str(exc)) from exc
        except LLMError as exc:
            steps.append(AgentStep(tool="parse_cv", status="error", detail="Profile extraction service is unavailable"))
            raise AgentToolError("parse_cv", "Profile extraction service is unavailable") from exc
        steps.append(AgentStep(tool="parse_cv", status="success"))

        # Step 2: search_jobs -- must use the profile just extracted, plus the
        # preferences supplied by the caller, unchanged. A failure here must
        # also stop the run: there is nothing real to explain otherwise.
        try:
            pipeline_result = await search_jobs_tool(
                self._search_pipeline, profile=profile, preferences=preferences,
            )
        except Exception as exc:
            logger.warning("search_jobs tool failed: %s: %s", type(exc).__name__, exc)
            steps.append(AgentStep(tool="search_jobs", status="error", detail="Search pipeline failed"))
            raise AgentToolError("search_jobs", "Search pipeline failed") from exc
        steps.append(AgentStep(tool="search_jobs", status="success"))

        # Step 3: explain_match -- best-effort only. Its own tool already
        # falls back per-offer to a deterministic explanation; this outer
        # guard is a last-resort safety net so a genuinely unexpected failure
        # here still returns the real search results instead of failing the
        # whole run.
        warnings: list[str] = []
        limit = max_explanations or self._max_explanations
        try:
            explanations = await explain_match_tool(
                self._llm_service, pipeline_result, profile, max_explanations=limit,
            )
            if any(item.source == "fallback" for item in explanations):
                warnings.append(
                    "Some offer explanations use a deterministic summary of the matching evidence "
                    "because the AI explanation service was unavailable or returned an invalid response."
                )
                steps.append(AgentStep(tool="explain_match", status="fallback"))
            else:
                steps.append(AgentStep(tool="explain_match", status="success"))
        except Exception as exc:
            logger.warning("explain_match tool failed unexpectedly: %s: %s", type(exc).__name__, exc)
            explanations = []
            warnings.append("Offer explanations are unavailable for this run.")
            steps.append(AgentStep(tool="explain_match", status="error", detail="Explanation step failed"))

        return AgentRunResult(
            profile=profile,
            preferences=preferences,
            pipeline_result=pipeline_result,
            explanations=explanations,
            steps=steps,
            warnings=warnings,
        )
