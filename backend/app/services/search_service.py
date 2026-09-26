"""Generic connector selection and RawOffer aggregation."""
from dataclasses import dataclass
import logging
from collections.abc import Sequence

from app.connectors.base import JobSourceConnector, RawOffer
from app.core.errors import AuthenticationError, ConnectorError, RateLimitError, SourceUnavailableError
from app.domain.search_criteria import SearchCriteria

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConnectorBinding:
    connector: JobSourceConnector
    enabled: bool = True


@dataclass(frozen=True)
class SourceFailure:
    source_name: str
    category: str


@dataclass(frozen=True)
class CollectionResult:
    offers: list[RawOffer]
    failures: list[SourceFailure]


class SearchService:
    def __init__(self, bindings: Sequence[ConnectorBinding] = ()) -> None:
        self._bindings = tuple(bindings)

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        return (await self.search_with_status(criteria)).offers

    async def search_with_status(self, criteria: SearchCriteria) -> CollectionResult:
        offers: list[RawOffer] = []
        failures: list[SourceFailure] = []
        for binding in self._bindings:
            if not binding.enabled:
                continue
            try:
                offers.extend(await binding.connector.search(criteria))
            except ConnectorError as exc:
                # Keep diagnostics useful without logging source payloads or user criteria.
                logger.warning(
                    "Job source connector failed; source=%s error_type=%s",
                    binding.connector.source_name,
                    type(exc).__name__,
                )
                if isinstance(exc, AuthenticationError):
                    category = "access_denied"
                elif isinstance(exc, RateLimitError):
                    category = "rate_limited"
                elif isinstance(exc, SourceUnavailableError):
                    category = "source_unavailable"
                else:
                    category = "connector_error"
                failures.append(SourceFailure(binding.connector.source_name, category))
        return CollectionResult(offers=offers, failures=failures)
