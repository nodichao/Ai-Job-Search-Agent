"""Generic connector selection and RawOffer aggregation."""
from dataclasses import dataclass
import logging
from collections.abc import Sequence

from app.connectors.base import JobSourceConnector, RawOffer
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConnectorBinding:
    connector: JobSourceConnector
    enabled: bool = True


class SearchService:
    def __init__(self, bindings: Sequence[ConnectorBinding] = ()) -> None:
        self._bindings = tuple(bindings)

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        offers: list[RawOffer] = []
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
        return offers
