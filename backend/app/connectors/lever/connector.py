"""Company/site-scoped adapter for Lever's documented Postings API."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from app.connectors.base import RawOffer
from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.pagination import PagePaginator
from app.core.config import Settings
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria

LEVER_API_ORIGIN = "https://api.lever.co"


@dataclass(frozen=True)
class LeverSiteContext:
    site: str
    company_name: str | None = None

    def __post_init__(self) -> None:
        if not self.site or not self.site.strip() or self.site in {".", ".."}:
            raise ValueError("A non-empty Lever SITE is required")


class LeverConnector:
    source_name = "Lever"

    def __init__(
        self,
        fetcher: HttpJsonFetcher,
        context: LeverSiteContext,
        *,
        page_size: int = 20,
        max_results: int | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if page_size < 1:
            raise ValueError("page_size must be positive")
        self.context = context
        self.endpoint = f"{LEVER_API_ORIGIN}/v0/postings/{quote(context.site.strip(), safe='')}"
        self._fetcher = fetcher
        self._page_size = page_size
        self._max_results = max_results or Settings.from_env().max_results_per_source
        if self._max_results < 1:
            raise ValueError("max_results must be positive")
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        """Fetch one explicit company's job board; no global criteria are supported."""
        del criteria  # The documented postings feed does not establish keyword filtering.

        async def fetch_page(skip: int, limit: int) -> list[RawOffer]:
            payload: Any = await self._fetcher.get(
                self.endpoint,
                params={"skip": skip, "limit": limit, "mode": "json"},
            )
            if not isinstance(payload, list):
                raise ConnectorError("Lever postings response must be a JSON list")
            retrieved_at = self._clock()
            offers: list[RawOffer] = []
            for index, item in enumerate(payload):
                if not isinstance(item, dict):
                    raise ConnectorError(f"Lever posting at page index {index} must be a JSON object")
                raw_id = item.get("id")
                source_id = str(raw_id) if isinstance(raw_id, (str, int)) and not isinstance(raw_id, bool) else None
                offers.append(
                    RawOffer(
                        source_name=self.source_name,
                        source_id=source_id,
                        payload=item,
                        retrieved_at=retrieved_at,
                        provenance={
                            "format": "json",
                            "request_url": self.endpoint,
                            "site": self.context.site,
                            "company_name": self.context.company_name,
                            "skip": skip,
                            "limit": limit,
                        },
                    )
                )
            return offers

        paginator = PagePaginator(fetch_page, page_size=self._page_size, max_results=self._max_results)
        results: list[RawOffer] = []
        async for page in paginator.pages():
            results.extend(page)
        return results
