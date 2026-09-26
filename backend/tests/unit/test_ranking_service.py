from app.domain.job_offer import JobOffer
from app.domain.matching import FilteringResult, MatchingResult
from app.domain.recommendation import (
    Recommendation,
    RecommendationCandidate,
    RecommendationDecision,
)
from app.services.ranking_service import RankingService


def candidate(source_id, *, score, confidence=0.5, decision=RecommendationDecision.RECOMMENDED,
              included=True, source="Example", title="Engineer"):
    offer = JobOffer.model_validate({
        "identity": {"sourceId": source_id, "offerUrl": f"https://jobs.example/{source_id}"},
        "source": {"name": source, "url": "https://jobs.example", "retrievedAt": "2026-01-01T00:00:00Z"},
        "position": {"title": title},
    })
    return RecommendationCandidate(
        offer=offer,
        filtering=FilteringResult(included=included),
        recommendation=Recommendation(decision=decision),
        matching=MatchingResult(score=score, confidence=confidence),
    )


def test_rank_order_uses_score_then_confidence_and_stable_identity_tie_break():
    candidates = [
        candidate("z", score=80, confidence=0.9),
        candidate("b", score=90, confidence=0.6),
        candidate("a", score=80, confidence=0.9),
        candidate("c", score=80, confidence=0.7),
    ]
    result = RankingService().rank(candidates)
    assert result.total == 4
    assert [(item.rank, item.offer.identity.source_id) for item in result.offers] == [
        (1, "b"), (2, "a"), (3, "z"), (4, "c")
    ]


def test_confidence_breaks_equal_score_ties_but_never_replaces_score():
    result = RankingService().rank([
        candidate("higher-confidence", score=70, confidence=1),
        candidate("higher-score", score=71, confidence=0.5),
        candidate("lower-confidence", score=70, confidence=0.5),
    ])
    assert [item.offer.identity.source_id for item in result.offers] == [
        "higher-score", "higher-confidence", "lower-confidence"
    ]


def test_rank_excludes_nonrecommended_filtered_out_and_missing_score_candidates():
    values = [
        candidate("yes", score=80),
        candidate("excluded", score=100, included=False),
        candidate("not-recommended", score=99, decision=RecommendationDecision.NOT_RECOMMENDED),
        candidate("insufficient", score=None, decision=RecommendationDecision.INSUFFICIENT_EVIDENCE),
        candidate("inconsistent", score=None, decision=RecommendationDecision.RECOMMENDED),
    ]
    result = RankingService().rank(values)
    assert result.total == 1
    assert [item.offer.identity.source_id for item in result.offers] == ["yes"]


def test_empty_and_repeated_ranking_are_deterministic_and_preserve_offer_provenance():
    service = RankingService()
    assert service.rank([]).offers == []
    values = [candidate("b", score=90), candidate("a", score=90)]
    first = service.rank(values)
    second = service.rank(values)
    assert first.model_dump() == second.model_dump()
    assert first.offers[0].offer.source.name == "Example"
    assert first.offers[0].offer.source.retrieved_at is not None
    assert first.offers[0].offer.identity.source_id == "a"
