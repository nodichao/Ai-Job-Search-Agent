import pytest

from app.domain.job_offer import (
    Employment, EmploymentType, JobOffer, OfferIdentity, OfferLocation, OfferSource, Position, Seniority,
)
from app.domain.matching import EvidenceStatus, FilteringResult, MatchDimension, MatchExplanation, MatchingResult
from app.domain.recommendation import RankedOffer, Recommendation, RecommendationDecision, RecommendationReason, RecommendationReasonCode, RankingResult
from app.domain.user_profile import UserProfile
from app.llm.schemas import MatchExplanationBatch, OfferExplanation
from app.services.agent_tools import (
    _build_explainable_match,
    _deterministic_explanation,
    explain_match_tool,
    select_offers_to_explain,
)
from app.services.search_pipeline import OfferAnalysis, SearchPipelineResult


def _offer(source_id: str, title: str = "Full-Stack Developer") -> JobOffer:
    return JobOffer(
        identity=OfferIdentity(sourceId=source_id),
        source=OfferSource(name="Fixture"),
        position=Position(title=title),
        location=OfferLocation(remote=True, countries=["Senegal"]),
        employment=Employment(type=EmploymentType.FULL_TIME, seniority=Seniority.JUNIOR),
    )


def _analysis(offer: JobOffer, *, score: float | None, decision: RecommendationDecision) -> OfferAnalysis:
    matching = MatchingResult(
        score=score, confidence=0.5,
        dimensions=[MatchDimension(name="roleAlignment", status=EvidenceStatus.SATISFIED, score=100)],
        matchedCriteria=["roleAlignment: title term overlap"], missingCriteria=[], conflicts=[],
    )
    filtering = FilteringResult(included=True, criteria=[], satisfiedCriteria=["jobTitles"], unknownCriteria=[], conflicts=[])
    explanation = MatchExplanation(
        score=score, confidence=0.5, dimensions=matching.dimensions,
        satisfiedCriteria=["jobTitles"], unknownCriteria=[], conflicts=[], reasons=["Offer retained by filtering."],
    )
    recommendation = Recommendation(
        decision=decision,
        reasons=[RecommendationReason(code=RecommendationReasonCode.SCORE_MEETS_THRESHOLD, message="Meets threshold", evidence=[])],
    )
    return OfferAnalysis(offer=offer, filtering=filtering, matching=matching, explanation=explanation, recommendation=recommendation)


def _pipeline_result(analyses: list[OfferAnalysis], ranked_ids: list[str]) -> SearchPipelineResult:
    by_id = {item.offer.identity.source_id: item for item in analyses}
    ranking = RankingResult(
        offers=[
            RankedOffer(rank=i + 1, offer=by_id[oid].offer, recommendation=by_id[oid].recommendation,
                        score=by_id[oid].matching.score, confidence=by_id[oid].matching.confidence)
            for i, oid in enumerate(ranked_ids)
        ],
        total=len(ranked_ids),
    )
    return SearchPipelineResult(offers=[item.offer for item in analyses], failures=[], analyses=analyses, ranking=ranking)


class FakeExplainLLM:
    def __init__(self, batch: MatchExplanationBatch | None = None, error: Exception | None = None):
        self.batch = batch
        self.error = error
        self.received: list = []

    async def explain_match(self, items):
        self.received = items
        if self.error:
            raise self.error
        return self.batch


def test_select_offers_to_explain_uses_ranking_order_first():
    offers = [_offer(f"o{i}") for i in range(3)]
    analyses = [
        _analysis(offers[0], score=90, decision=RecommendationDecision.RECOMMENDED),
        _analysis(offers[1], score=40, decision=RecommendationDecision.NOT_RECOMMENDED),
        _analysis(offers[2], score=95, decision=RecommendationDecision.RECOMMENDED),
    ]
    result = _pipeline_result(analyses, ranked_ids=["o2", "o0"])

    selected = select_offers_to_explain(result, max_explanations=5)

    assert [item.offer.identity.source_id for _, item in selected] == ["o2", "o0", "o1"]


def test_select_offers_to_explain_respects_the_limit():
    offers = [_offer(f"o{i}") for i in range(3)]
    analyses = [_analysis(offer, score=50, decision=RecommendationDecision.NOT_RECOMMENDED) for offer in offers]
    result = _pipeline_result(analyses, ranked_ids=[])

    selected = select_offers_to_explain(result, max_explanations=2)

    assert len(selected) == 2


def test_select_offers_to_explain_returns_nothing_for_empty_pipeline():
    result = _pipeline_result([], ranked_ids=[])
    assert select_offers_to_explain(result, max_explanations=5) == []


def test_build_explainable_match_carries_real_evidence_only():
    offer = _offer("o1", title="Full-Stack Developer")
    analysis = _analysis(offer, score=77.5, decision=RecommendationDecision.RECOMMENDED)
    profile = UserProfile(skills=["Python"], jobTitles=["Full-Stack Developer"], totalExperienceYears=3)

    item = _build_explainable_match("offer-0", analysis, profile)

    assert item.offer_id == "offer-0"
    assert item.offer.title == "Full-Stack Developer"
    assert item.score == 77.5
    assert item.decision == "RECOMMENDED"
    assert item.candidate.skills == ["Python"]
    assert item.satisfied_criteria == ["jobTitles"]


def test_deterministic_explanation_never_invents_a_different_decision():
    offer = _offer("o1")
    analysis = _analysis(offer, score=42.0, decision=RecommendationDecision.NOT_RECOMMENDED)

    fallback = _deterministic_explanation("offer-0", analysis)

    assert fallback.offer_id == "offer-0"
    assert "NOT_RECOMMENDED" in fallback.summary
    assert fallback.recommendation_context == "Meets threshold"


@pytest.mark.asyncio
async def test_explain_match_tool_uses_llm_result_when_available():
    offer = _offer("o1")
    analysis = _analysis(offer, score=90, decision=RecommendationDecision.RECOMMENDED)
    result = _pipeline_result([analysis], ranked_ids=["o1"])
    llm = FakeExplainLLM(batch=MatchExplanationBatch(explanations=[
        OfferExplanation(offerId="o1", summary="Strong match.", recommendationContext="Meets threshold"),
    ]))

    explained = await explain_match_tool(llm, result, UserProfile(), max_explanations=5)

    assert len(explained) == 1
    assert explained[0].offer_id == "o1"
    assert explained[0].source == "llm"
    assert explained[0].explanation.summary == "Strong match."
    assert len(llm.received) == 1


@pytest.mark.asyncio
async def test_explain_match_tool_falls_back_deterministically_on_llm_failure():
    offer = _offer("o1")
    analysis = _analysis(offer, score=90, decision=RecommendationDecision.RECOMMENDED)
    result = _pipeline_result([analysis], ranked_ids=["o1"])
    llm = FakeExplainLLM(error=RuntimeError("provider down"))

    explained = await explain_match_tool(llm, result, UserProfile(), max_explanations=5)

    assert len(explained) == 1
    assert explained[0].source == "fallback"
    assert "RECOMMENDED" in explained[0].explanation.summary


@pytest.mark.asyncio
async def test_explain_match_tool_falls_back_per_offer_when_llm_response_is_incomplete():
    offers = [_offer("o1"), _offer("o2")]
    analyses = [_analysis(offer, score=80, decision=RecommendationDecision.RECOMMENDED) for offer in offers]
    result = _pipeline_result(analyses, ranked_ids=["o1", "o2"])
    llm = FakeExplainLLM(batch=MatchExplanationBatch(explanations=[
        OfferExplanation(offerId="o1", summary="Only this one was returned.", recommendationContext="Meets threshold"),
    ]))

    explained = await explain_match_tool(llm, result, UserProfile(), max_explanations=5)

    by_id = {item.offer_id: item for item in explained}
    assert by_id["o1"].source == "llm"
    assert by_id["o2"].source == "fallback"


@pytest.mark.asyncio
async def test_explain_match_tool_returns_empty_list_for_no_offers():
    result = _pipeline_result([], ranked_ids=[])
    llm = FakeExplainLLM(batch=MatchExplanationBatch(explanations=[]))

    explained = await explain_match_tool(llm, result, UserProfile(), max_explanations=5)

    assert explained == []
    assert llm.received == []
