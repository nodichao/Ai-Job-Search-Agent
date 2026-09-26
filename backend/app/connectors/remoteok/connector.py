"""RemoteOK JSON collection. Endpoint injection is required because project docs do not establish its URL."""
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from app.connectors.base import RawOffer
from app.connectors.common.http import HttpJsonFetcher
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria


def _validate_endpoint(endpoint: str) -> tuple[str, str]:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("RemoteOK endpoint must be an absolute HTTP(S) URL without embedded credentials")
    source_url = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
    # The endpoint may contain deployment parameters; never copy those into provenance.
    safe_endpoint = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return safe_endpoint, source_url


class RemoteOKConnector:
    source_name = "RemoteOK"

    def __init__(
        self,
        fetcher: HttpJsonFetcher,
        endpoint: str,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._request_url = endpoint
        self.endpoint, self.source_url = _validate_endpoint(endpoint)
        self._fetcher = fetcher
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        """Fetch the documented JSON feed; criteria are accepted but not translated.

        No RemoteOK query parameter or pagination behavior is established in the
        project references, so this method deliberately sends neither.
        """
        del criteria
        payload: Any = await self._fetcher.get(self._request_url)
        if not isinstance(payload, list):
            raise ConnectorError("RemoteOK JSON response must be a list")

        retrieved_at = self._clock()
        offers: list[RawOffer] = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise ConnectorError(f"RemoteOK item at index {index} must be a JSON object")
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
                        "source_url": self.source_url,
                        "request_url": self.endpoint,
                        "item_index": index,
                        "attribution_required": True,
                        "source_link_required": True,
                    },
                )
            )
        return offers
