import pytest

from app.core.errors import LLMError
from app.domain.job_offer import JobOffer, OfferIdentity, OfferSource, Position
from app.domain.matching import EvidenceStatus, FilteringResult, MatchDimension, MatchExplanation, MatchingResult
from app.domain.recommendation import RankedOffer, Recommendation, RecommendationDecision, RankingResult
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.llm.schemas import MatchExplanationBatch, OfferExplanation
from app.services.agent_service import AgentService
from app.services.agent_tools import AgentToolError
from app.services.cv_document_extractor import CvDocumentError
from app.services.search_pipeline import OfferAnalysis, SearchPipelineResult


class FakeProfileService:
    def __init__(self, profile: UserProfile | None = None, error: Exception | None = None):
        self.profile = profile
        self.error = error
        self.calls = []

    async def parse_cv_file(self, filename, media_type, content):
        self.calls.append((filename, media_type, content))
        if self.error:
            raise self.error
        return self.profile


class FakePipeline:
    def __init__(self, result: SearchPipelineResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = []

    async def search(self, criteria, profile, preferences):
        self.calls.append((criteria, profile, preferences))
        if self.error:
            raise self.error
        return self.result


class FakeLLM:
    def __init__(self, batch: MatchExplanationBatch | None = None, error: Exception | None = None):
        self.batch = batch
        self.error = error

    async def explain_match(self, items):
        if self.error:
            raise self.error
        return self.batch


def _offer() -> JobOffer:
    return JobOffer(identity=OfferIdentity(sourceId="o1"), source=OfferSource(name="Fixture"),
                     position=Position(title="Full-Stack Developer"))


def _pipeline_result_with_one_recommended() -> SearchPipelineResult:
    offer = _offer()
    matching = MatchingResult(score=90, confidence=0.8, dimensions=[
        MatchDimension(name="roleAlignment", status=EvidenceStatus.SATISFIED, score=100),
    ])
    filtering = FilteringResult(included=True, satisfiedCriteria=["jobTitles"])
    explanation = MatchExplanation(score=90, confidence=0.8, dimensions=matching.dimensions,
                                    satisfiedCriteria=["jobTitles"], reasons=["Offer retained."])
    recommendation = Recommendation(decision=RecommendationDecision.RECOMMENDED)
    analysis = OfferAnalysis(offer=offer, filtering=filtering, matching=matching,
                              explanation=explanation, recommendation=recommendation)
    ranking = RankingResult(offers=[RankedOffer(rank=1, offer=offer, recommendation=recommendation, score=90, confidence=0.8)], total=1)
    return SearchPipelineResult(offers=[offer], failures=[], analyses=[analysis], ranking=ranking)


@pytest.mark.asyncio
async def test_full_run_calls_tools_in_order_and_preserves_pipeline_output():
    profile = UserProfile(skills=["Python"])
    pipeline_result = _pipeline_result_with_one_recommended()
    profile_service = FakeProfileService(profile=profile)
    pipeline = FakePipeline(result=pipeline_result)
    llm = FakeLLM(batch=MatchExplanationBatch(explanations=[
        OfferExplanation(offerId="o1", summary="Great fit.", recommendationContext="Meets threshold"),
    ]))
    agent = AgentService(profile_service, pipeline, llm, max_explanations=5)

    result = await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"%PDF-1.4 fake",
                              preferences=SearchPreferences())

    assert [step.tool for step in result.steps] == ["parse_cv", "search_jobs", "explain_match"]
    assert all(step.status == "success" for step in result.steps)
    assert profile_service.calls == [("cv.pdf", "application/pdf", b"%PDF-1.4 fake")]
    assert pipeline.calls[0][1] is profile
    # Non-regression: the agent must not alter the pipeline's own score/rank/decision.
    assert result.pipeline_result.ranking.offers[0].score == 90
    assert result.pipeline_result.ranking.offers[0].confidence == 0.8
    assert result.pipeline_result.analyses[0].recommendation.decision is RecommendationDecision.RECOMMENDED
    assert result.pipeline_result is pipeline_result
    assert result.explanations[0].source == "llm"
    assert result.warnings == []


@pytest.mark.asyncio
async def test_parse_cv_failure_stops_before_search_jobs():
    profile_service = FakeProfileService(error=CvDocumentError("Uploaded CV is empty"))
    pipeline = FakePipeline(result=_pipeline_result_with_one_recommended())
    agent = AgentService(profile_service, pipeline, FakeLLM(), max_explanations=5)

    with pytest.raises(AgentToolError) as exc:
        await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"", preferences=SearchPreferences())

    assert exc.value.tool == "parse_cv"
    assert pipeline.calls == []


@pytest.mark.asyncio
async def test_parse_cv_llm_failure_is_reported_as_parse_cv_step():
    profile_service = FakeProfileService(error=LLMError("provider down"))
    pipeline = FakePipeline(result=_pipeline_result_with_one_recommended())
    agent = AgentService(profile_service, pipeline, FakeLLM(), max_explanations=5)

    with pytest.raises(AgentToolError) as exc:
        await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"x", preferences=SearchPreferences())

    assert exc.value.tool == "parse_cv"


@pytest.mark.asyncio
async def test_search_jobs_failure_stops_before_explain_match():
    profile_service = FakeProfileService(profile=UserProfile())
    pipeline = FakePipeline(error=RuntimeError("connector exploded"))
    llm = FakeLLM()
    agent = AgentService(profile_service, pipeline, llm, max_explanations=5)

    with pytest.raises(AgentToolError) as exc:
        await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"x", preferences=SearchPreferences())

    assert exc.value.tool == "search_jobs"


@pytest.mark.asyncio
async def test_explain_match_failure_falls_back_without_failing_the_run():
    profile_service = FakeProfileService(profile=UserProfile())
    pipeline_result = _pipeline_result_with_one_recommended()
    pipeline = FakePipeline(result=pipeline_result)
    llm = FakeLLM(error=RuntimeError("provider down"))
    agent = AgentService(profile_service, pipeline, llm, max_explanations=5)

    result = await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"x", preferences=SearchPreferences())

    assert result.pipeline_result is pipeline_result
    assert result.explanations[0].source == "fallback"
    assert any("deterministic summary" in warning for warning in result.warnings)
    explain_step = next(step for step in result.steps if step.tool == "explain_match")
    assert explain_step.status == "fallback"


@pytest.mark.asyncio
async def test_max_explanations_override_is_respected():
    profile_service = FakeProfileService(profile=UserProfile())
    pipeline_result = _pipeline_result_with_one_recommended()
    pipeline = FakePipeline(result=pipeline_result)
    received = {}

    class RecordingLLM:
        async def explain_match(self, items):
            received["items"] = items
            return MatchExplanationBatch(explanations=[])

    agent = AgentService(profile_service, pipeline, RecordingLLM(), max_explanations=5)
    await agent.run(filename="cv.pdf", media_type="application/pdf", content=b"x",
                     preferences=SearchPreferences(), max_explanations=1)

    assert len(received["items"]) == 1
