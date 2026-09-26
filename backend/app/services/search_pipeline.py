"""Orchestrate collection and normalization without merging their services."""
from dataclasses import dataclass

from app.domain.job_offer import JobOffer
from app.domain.matching import FilteringResult, MatchExplanation, MatchingResult
from app.domain.search_criteria import SearchCriteria
from app.domain.search_preferences import SearchPreferences
from app.domain.user_profile import UserProfile
from app.services.explanation_service import ExplanationService
from app.services.filtering_service import FilteringService
from app.services.matching_service import MatchingService
from app.services.normalization_service import NormalizationService
from app.services.search_service import SearchService, SourceFailure


@dataclass(frozen=True)
class SearchPipelineResult:
    offers: list[JobOffer]
    failures: list[SourceFailure]
    analyses: list["OfferAnalysis"]

    @property
    def included_offers(self) -> list[JobOffer]:
        return [item.offer for item in self.analyses if item.filtering.included]


@dataclass(frozen=True)
class OfferAnalysis:
    offer: JobOffer
    filtering: FilteringResult
    matching: MatchingResult
    explanation: MatchExplanation


class SearchPipeline:
    def __init__(
        self,
        search_service: SearchService,
        normalization_service: NormalizationService,
        filtering_service: FilteringService | None = None,
        matching_service: MatchingService | None = None,
        explanation_service: ExplanationService | None = None,
    ) -> None:
        self._search_service = search_service
        self._normalization_service = normalization_service
        self._filtering_service = filtering_service or FilteringService()
        self._matching_service = matching_service or MatchingService()
        self._explanation_service = explanation_service or ExplanationService()

    async def search(
        self,
        criteria: SearchCriteria,
        profile: UserProfile | None = None,
        preferences: SearchPreferences | None = None,
    ) -> SearchPipelineResult:
        collection = await self._search_service.search_with_status(criteria)
        offers = self._normalization_service.normalize(collection.offers)
        profile = profile or UserProfile()
        preferences = preferences or SearchPreferences()
        filtering = self._filtering_service.filter(criteria, offers, preferences.preference_strength)
        analyses = [
            OfferAnalysis(
                offer=offer,
                filtering=decision,
                matching=matching,
                explanation=self._explanation_service.explain(decision, matching),
            )
            for offer, decision in filtering
            for matching in [self._matching_service.match(profile, preferences, offer)]
        ]
        return SearchPipelineResult(
            offers=offers,
            failures=collection.failures,
            analyses=analyses,
        )
