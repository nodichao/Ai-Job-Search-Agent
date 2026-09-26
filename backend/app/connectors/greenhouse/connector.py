"""Board-scoped Greenhouse transport boundary; response schema is not verified in project docs."""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from urllib.parse import urlsplit, urlunsplit

from app.connectors.base import RawOffer
from app.connectors.common.http import HttpJsonFetcher
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria


@dataclass(frozen=True)
class GreenhouseBoardContext:
    board_token: str
    company_name: str | None = None
    company_id: str | None = None

    def __post_init__(self) -> None:
        if not self.board_token or not self.board_token.strip():
            raise ValueError("A Greenhouse board token/context is required")


@dataclass(frozen=True)
class GreenhouseBoardOffer:
    """A record produced by a parser configured against a verified board schema."""
    source_id: str | None
    payload: dict[str, Any]


class GreenhouseResponseParser(Protocol):
    def parse(self, response: Any, context: GreenhouseBoardContext) -> Sequence[GreenhouseBoardOffer]: ...


class GreenhouseConnector:
    source_name = "Greenhouse"

    def __init__(
        self,
        fetcher: HttpJsonFetcher,
        context: GreenhouseBoardContext,
        *,
        endpoint: str,
        parser: GreenhouseResponseParser,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Require an explicitly configured endpoint and verified parser.

        The project references do not specify Greenhouse's endpoint form or
        response fields; this class therefore does not build either one.
        """
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Greenhouse endpoint must be an absolute HTTP(S) URL without embedded credentials")
        self.endpoint = endpoint
        self.source_url = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
        self.context = context
        self._fetcher = fetcher
        self._parser = parser
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        """Fetch the explicitly configured board; no unverified filters are sent."""
        del criteria
        response = await self._fetcher.get(self.endpoint)
        try:
            records = self._parser.parse(response, self.context)
        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError("Configured Greenhouse parser rejected the board response") from exc
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            raise ConnectorError("Configured Greenhouse parser must return a sequence of board offers")

        retrieved_at = self._clock()
        offers: list[RawOffer] = []
        for record in records:
            if not isinstance(record, GreenhouseBoardOffer):
                raise ConnectorError("Configured Greenhouse parser returned an invalid board offer")
            offers.append(
                RawOffer(
                    source_name=self.source_name,
                    source_id=record.source_id,
                    payload=record.payload,
                    retrieved_at=retrieved_at,
                    provenance={
                        "format": "json",
                        "request_url": self.endpoint,
                        "source_url": self.source_url,
                        "board_token": self.context.board_token,
                        "company_name": self.context.company_name,
                        "company_id": self.context.company_id,
                    },
                )
            )
        return offers
