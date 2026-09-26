"""Deterministic presentation ordering for offers that pass recommendation."""
from collections.abc import Sequence

from app.domain.recommendation import (
    RankedOffer,
    RankingResult,
    RecommendationCandidate,
    RecommendationDecision,
)


class RankingService:
    def rank(self, candidates: Sequence[RecommendationCandidate]) -> RankingResult:
        eligible = [
            candidate for candidate in candidates
            if candidate.filtering.included
            and candidate.recommendation.decision is RecommendationDecision.RECOMMENDED
            and candidate.matching.score is not None
        ]
        ordered = sorted(enumerate(eligible), key=lambda pair: self._sort_key(pair[1], pair[0]))
        ranked = [
            RankedOffer(
                rank=position,
                offer=candidate.offer,
                recommendation=candidate.recommendation,
                score=candidate.matching.score,
                confidence=candidate.matching.confidence,
            )
            for position, (_, candidate) in enumerate(ordered, start=1)
        ]
        return RankingResult(offers=ranked, total=len(ranked))

    @staticmethod
    def _sort_key(candidate: RecommendationCandidate, original_index: int) -> tuple[object, ...]:
        offer = candidate.offer
        identity = offer.identity
        return (
            -candidate.matching.score,  # type: ignore[operator] -- null scores were excluded above
            -candidate.matching.confidence,
            offer.source.name.casefold(),
            (identity.source_id or identity.id or identity.slug or "").casefold(),
            str(identity.offer_url or "").casefold(),
            (offer.company.name or "").casefold(),
            offer.position.title.casefold(),
            original_index,
        )
