"""Orchestrate collection and normalization without merging their services."""
from dataclasses import dataclass

from app.domain.job_offer import JobOffer
from app.domain.search_criteria import SearchCriteria
from app.services.normalization_service import NormalizationService
from app.services.search_service import SearchService, SourceFailure


@dataclass(frozen=True)
class SearchPipelineResult:
    offers: list[JobOffer]
    failures: list[SourceFailure]


class SearchPipeline:
    def __init__(self, search_service: SearchService, normalization_service: NormalizationService) -> None:
        self._search_service = search_service
        self._normalization_service = normalization_service

    async def search(self, criteria: SearchCriteria) -> SearchPipelineResult:
        collection = await self._search_service.search_with_status(criteria)
        return SearchPipelineResult(
            offers=self._normalization_service.normalize(collection.offers),
            failures=collection.failures,
        )
