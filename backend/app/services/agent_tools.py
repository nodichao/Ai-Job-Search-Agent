"""Thin adapters exposing existing services as the agent's three bounded tools.

None of these tools re-implement or recompute anything: `parse_cv` delegates
to `ProfileService`, `search_jobs` delegates to the existing `SearchPipeline`,
and `explain_match` delegates to the configured `LLMService`, falling back to
the deterministic `MatchExplanation` the pipeline already computed for every
offer when the LLM call is unavailable or invalid. No score, rank, or
recommendation decision is ever recalculated here.
"""
from dataclasses import dataclass
from typing import Literal

from app.core.errors import JobAgentError
from app.domain.job_offer import JobOffer
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.llm.base import LLMService
from app.llm.schemas import (
    ExplainableCandidate,
    ExplainableDimension,
    ExplainableMatch,
    ExplainableOfferFacts,
    OfferExplanation,
)
from app.services.profile_service import ProfileService
from app.services.search_criteria_builder import criteria_from_preferences
from app.services.search_pipeline import OfferAnalysis, SearchPipeline, SearchPipelineResult


class AgentToolError(JobAgentError):
    """A named, non-fatal-by-default failure raised by one agent tool."""

    def __init__(self, tool: str, message: str):
        super().__init__(message)
        self.tool = tool


def _offer_key(offer: JobOffer) -> tuple[str | None, str | None, str | None, str | None]:
    """Identity used to correlate a ranked/selected offer back to its full
    analysis, without relying on Python object identity across service
    boundaries."""
    identity = offer.identity
    return (identity.source_id, identity.id, identity.slug,
            str(identity.offer_url) if identity.offer_url else None)


def _stable_offer_id(offer: JobOffer, fallback_index: int) -> str:
    """The offer's own real identity (matching `offerIdentity.sourceId` in
    `OfferMatchView`), so a caller can join an explanation back to the exact
    offer it describes without guessing a position-based index. Only falls
    back to a positional placeholder when the offer truly has no identity
    evidence at all."""
    identity = offer.identity
    return identity.source_id or identity.id or identity.slug or f"offer-{fallback_index}"


async def parse_cv_tool(
    profile_service: ProfileService,
    *,
    filename: str,
    media_type: str | None,
    content: bytes,
) -> UserProfile:
    """Tool 1: extract a structured profile from the uploaded CV.

    Raises `CvDocumentError` (invalid/unreadable file) or `LLMError`
    (extraction provider failure) -- both already carry safe, user-facing
    messages from `ProfileService`/`CvDocumentExtractor`.
    """
    return await profile_service.parse_cv_file(filename, media_type, content)


async def search_jobs_tool(
    pipeline: SearchPipeline,
    *,
    profile: UserProfile,
    preferences: SearchPreferences,
) -> SearchPipelineResult:
    """Tool 2: run the existing search/filter/match/rank pipeline unchanged."""
    criteria: SearchCriteria = criteria_from_preferences(preferences)
    return await pipeline.search(criteria, profile, preferences)


ExplanationSource = Literal["llm", "fallback"]


@dataclass(frozen=True)
class ExplainedOffer:
    offer_id: str
    source: ExplanationSource
    explanation: OfferExplanation


def _profile_for_llm(profile: UserProfile) -> ExplainableCandidate:
    return ExplainableCandidate(
        jobTitles=profile.job_titles,
        skills=profile.skills,
        totalExperienceYears=profile.total_experience_years,
        education=profile.education,
        languages=profile.languages,
    )


def _offer_facts_for_llm(offer: JobOffer) -> ExplainableOfferFacts:
    return ExplainableOfferFacts(
        title=offer.position.title,
        company=offer.company.name,
        locations=offer.location.locations,
        countries=offer.location.countries,
        remote=offer.location.remote,
        remoteScope=offer.location.remote_scope.value,
        employmentType=offer.employment.type.value,
        seniority=offer.employment.seniority.value,
    )


def select_offers_to_explain(
    pipeline_result: SearchPipelineResult,
    max_explanations: int,
) -> list[tuple[str, OfferAnalysis]]:
    """Pick offers to explain using only the engine's own ranking/ordering.

    Recommended offers (already ranked by `RankingService`) come first, in
    the engine's own order. If there is room left, the highest-scoring
    remaining retained offers (not recommended, or insufficient evidence)
    fill the rest, so a run with few/no recommendations still gets useful
    "why not" context -- still ordered strictly by the engine's own score,
    never re-ranked here.
    """
    by_key = {_offer_key(item.offer): item for item in pipeline_result.analyses}
    selected: list[tuple[str, OfferAnalysis]] = []
    seen: set[tuple] = set()

    for ranked in pipeline_result.ranking.offers[:max_explanations]:
        key = _offer_key(ranked.offer)
        analysis = by_key.get(key)
        if analysis is None or key in seen:
            continue
        selected.append((_stable_offer_id(analysis.offer, len(selected)), analysis))
        seen.add(key)

    if len(selected) < max_explanations:
        remaining = [
            item for item in pipeline_result.analyses
            if item.filtering.included and _offer_key(item.offer) not in seen and item.matching.score is not None
        ]
        remaining.sort(key=lambda item: item.matching.score, reverse=True)
        for item in remaining:
            if len(selected) >= max_explanations:
                break
            selected.append((_stable_offer_id(item.offer, len(selected)), item))
            seen.add(_offer_key(item.offer))

    return selected


def _build_explainable_match(offer_id: str, analysis: OfferAnalysis, profile: UserProfile) -> ExplainableMatch:
    return ExplainableMatch(
        offerId=offer_id,
        offer=_offer_facts_for_llm(analysis.offer),
        candidate=_profile_for_llm(profile),
        score=analysis.matching.score,
        confidence=analysis.matching.confidence,
        decision=analysis.recommendation.decision.value,
        decisionReasons=[reason.message for reason in analysis.recommendation.reasons],
        satisfiedCriteria=analysis.explanation.satisfied_criteria,
        unknownCriteria=analysis.explanation.unknown_criteria,
        conflicts=analysis.explanation.conflicts,
        dimensions=[
            ExplainableDimension(name=d.name, status=d.status.value, score=d.score, evidence=d.evidence)
            for d in analysis.matching.dimensions
        ],
    )


def _deterministic_explanation(offer_id: str, analysis: OfferAnalysis) -> OfferExplanation:
    """Build a fallback explanation from data already computed by
    `ExplanationService`/`MatchingService` -- no LLM involved, no new facts."""
    explanation = analysis.explanation
    decision = analysis.recommendation.decision.value
    score_text = f"score {explanation.score:g}/100" if explanation.score is not None else "no calculable score"
    return OfferExplanation(
        offerId=offer_id,
        summary=f"Deterministic engine result: {decision} ({score_text}, confidence {explanation.confidence:g}).",
        strengths=[item for item in explanation.satisfied_criteria],
        gaps=[item for item in explanation.unknown_criteria],
        constraints=[item for item in explanation.conflicts],
        uncertainties=[item for item in explanation.unknown_criteria],
        recommendationContext=(
            analysis.recommendation.reasons[0].message if analysis.recommendation.reasons
            else "No reason was recorded for this decision."
        ),
        nextSteps=[
            "This explanation is a deterministic summary of the matching engine's own evidence; "
            "the AI explanation service was unavailable for this offer.",
        ],
    )


async def explain_match_tool(
    llm_service: LLMService,
    pipeline_result: SearchPipelineResult,
    profile: UserProfile,
    *,
    max_explanations: int,
) -> list[ExplainedOffer]:
    """Tool 3: explain the top offers selected by the engine's own ranking.

    Tries one batched LLM call for all selected offers; on any failure
    (unavailable provider, invalid/incomplete structured output), falls back
    per-offer to the deterministic explanation already computed by the
    pipeline. A search never fails solely because this step failed.
    """
    selected = select_offers_to_explain(pipeline_result, max_explanations)
    if not selected:
        return []

    items = [_build_explainable_match(offer_id, analysis, profile) for offer_id, analysis in selected]

    try:
        batch = await llm_service.explain_match(items)
        by_id = {item.offer_id: item for item in batch.explanations}
        results: list[ExplainedOffer] = []
        for offer_id, analysis in selected:
            narrative = by_id.get(offer_id)
            if narrative is None:
                results.append(ExplainedOffer(offer_id, "fallback", _deterministic_explanation(offer_id, analysis)))
            else:
                results.append(ExplainedOffer(offer_id, "llm", narrative))
        return results
    except Exception:
        return [
            ExplainedOffer(offer_id, "fallback", _deterministic_explanation(offer_id, analysis))
            for offer_id, analysis in selected
        ]
