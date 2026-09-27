"""Public Himalayas JSON feed connector."""
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from app.connectors.base import RawOffer
from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.pagination import CursorPaginator
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria


class HimalayasConnector:
    source_name = "Himalayas"
    endpoint = "https://himalayas.app/jobs/api"
    page_size = 20

    def __init__(
        self,
        fetcher: HttpJsonFetcher,
        *,
        max_results: int = 100,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if max_results < 1:
            raise ValueError("max_results must be positive")
        parsed = urlsplit(self.endpoint)
        if parsed.scheme != "https" or parsed.hostname != "himalayas.app":
            raise ValueError("Himalayas endpoint must use its documented HTTPS host")
        self._fetcher = fetcher
        self._max_results = max_results
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        """Read the documented browse feed; generic criteria are not inferred into filters."""
        del criteria

        async def fetch_page(cursor: str | None) -> object:
            params: dict[str, object] = {"limit": min(self.page_size, self._max_results)}
            if cursor is not None:
                params["cursor"] = cursor
            return await self._fetcher.get(self.endpoint, params=params)

        def cursor_for(page: object) -> str | None:
            if not isinstance(page, dict):
                raise ConnectorError("Himalayas response must be a JSON object")
            jobs = page.get("jobs")
            if not isinstance(jobs, list):
                raise ConnectorError("Himalayas response must contain a jobs array")
            token = page.get("nextCursor")
            if token is not None and (not isinstance(token, str) or not token):
                raise ConnectorError("Himalayas nextCursor must be a non-empty string")
            return token

        paginator = CursorPaginator(fetch_page, cursor_for)
        offers: list[RawOffer] = []
        page_number = 0
        async for page in _limited_pages(paginator, self._max_results):
            page_number += 1
            if not isinstance(page, dict) or not isinstance(page.get("jobs"), list):
                raise ConnectorError("Himalayas response must contain a jobs array")
            jobs = page["jobs"]
            retrieved_at = self._clock()
            for item_index, item in enumerate(jobs):
                if not isinstance(item, dict):
                    raise ConnectorError("Himalayas job entries must be JSON objects")
                raw_id = item.get("guid")
                source_id = raw_id.strip() if isinstance(raw_id, str) and raw_id.strip() else None
                offers.append(RawOffer(
                    source_name=self.source_name,
                    source_id=source_id,
                    payload=item,
                    retrieved_at=retrieved_at,
                    provenance={
                        "format": "json",
                        "source_url": "https://himalayas.app/",
                        "request_url": self.endpoint,
                        "page_number": page_number,
                        "item_index": item_index,
                        "response_updated_at": page.get("updatedAt"),
                        "attribution_required": True,
                        "source_link_required": True,
                    },
                ))
                if len(offers) >= self._max_results:
                    return offers
        return offers


async def _limited_pages(paginator: CursorPaginator, max_results: int):
    yielded = 0
    async for page in paginator.pages():
        yield page
        if isinstance(page, dict) and isinstance(page.get("jobs"), list):
            yielded += len(page["jobs"])
        if yielded >= max_results:
            return
