import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.retry import RetryPolicy
from app.connectors.remoteok.connector import RemoteOKConnector
from app.core.errors import AuthenticationError, ConnectorError, RateLimitError, SourceUnavailableError
from app.domain.search_criteria import SearchCriteria

FIXTURES = Path(__file__).parents[1] / "fixtures" / "remoteok"
ENDPOINT = "https://remoteok.example.invalid/jobs.json"
RETRIEVED_AT = datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc)


def _fixture(name: str) -> list[dict[str, object]]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_connector_preserves_payload_source_id_retrieval_and_provenance() -> None:
    source_payload = _fixture("offer_list.json")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=source_payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = RemoteOKConnector(
            HttpJsonFetcher(client=client), ENDPOINT,
            clock=lambda: RETRIEVED_AT,
        )
        offers = await connector.search(SearchCriteria(keywords=["platform"], countries=["SN"]))

    assert len(offers) == 1
    raw = offers[0]
    assert raw.source_name == "RemoteOK"
    assert raw.source_id == "735421"
    assert raw.payload == source_payload[0]
    assert raw.retrieved_at == RETRIEVED_AT
    assert raw.provenance == {
        "format": "json",
        "source_url": "https://remoteok.example.invalid/",
        "request_url": ENDPOINT,
        "item_index": 0,
        "attribution_required": True,
        "source_link_required": True,
    }
    assert seen[0].url.query == b""  # Criteria are not translated to undocumented query parameters.


@pytest.mark.asyncio
async def test_connector_keeps_partial_source_entries_and_original_payload() -> None:
    partial_payload = _fixture("partial_offer_list.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=partial_payload))) as client:
        offers = await RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT, clock=lambda: RETRIEVED_AT).search(SearchCriteria())
    assert offers[0].source_id is None
    assert offers[0].payload == partial_payload[0]


@pytest.mark.asyncio
async def test_connector_skips_documented_feed_metadata_and_carries_attribution_notice():
    offer_payload = _fixture("offer_list.json")[0]
    metadata = {
        "last_updated": 1790438426,
        "legal": "Credit Remote OK as source and link the original job URL.",
    }
    response_body = [metadata, offer_payload]
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json=response_body)
    )) as client:
        offers = await RemoteOKConnector(
            HttpJsonFetcher(client=client), ENDPOINT, clock=lambda: RETRIEVED_AT
        ).search(SearchCriteria())

    assert len(offers) == 1
    assert offers[0].payload == offer_payload
    assert offers[0].source_id == "735421"
    assert offers[0].provenance["item_index"] == 1
    assert offers[0].provenance["feed_last_updated"] == 1790438426
    assert offers[0].provenance["attribution_notice"] == metadata["legal"]


@pytest.mark.asyncio
async def test_connector_rejects_malformed_feed_metadata():
    response_body = [{"last_updated": "recent", "legal": "terms"}]
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json=response_body)
    )) as client:
        with pytest.raises(ConnectorError, match="metadata is malformed"):
            await RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT).search(SearchCriteria())


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"jobs": []}, ["not-an-object"]])
async def test_connector_rejects_invalid_feed_shapes(body: object) -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))) as client:
        connector = RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT)
        with pytest.raises(ConnectorError):
            await connector.search(SearchCriteria())


@pytest.mark.asyncio
async def test_connector_reports_invalid_json() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"not-json"))) as client:
        connector = RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT)
        with pytest.raises(ConnectorError):
            await connector.search(SearchCriteria())


@pytest.mark.asyncio
async def test_connector_reports_timeout_as_transient_unavailability() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
        fetcher = HttpJsonFetcher(client=client, retry_policy=RetryPolicy(max_attempts=1))
        connector = RemoteOKConnector(fetcher, ENDPOINT)
        with pytest.raises(SourceUnavailableError, match="timed out"):
            await connector.search(SearchCriteria())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error"),
    [(401, AuthenticationError), (403, AuthenticationError), (404, ConnectorError), (429, RateLimitError)],
)
async def test_connector_does_not_retry_access_or_client_errors(status: int, error: type[Exception]) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT)
        with pytest.raises(error):
            await connector.search(SearchCriteria())
    assert calls == 1


@pytest.mark.asyncio
async def test_connector_retries_transient_server_errors_only_with_bounded_policy() -> None:
    calls = 0
    payload = _fixture("offer_list.json")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503) if calls == 1 else httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpJsonFetcher(client=client, retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0))
        offers = await RemoteOKConnector(fetcher, ENDPOINT, clock=lambda: RETRIEVED_AT).search(SearchCriteria())
    assert calls == 2
    assert offers[0].source_id == "735421"


def test_endpoint_is_required_and_must_not_embed_credentials() -> None:
    with pytest.raises(TypeError):
        RemoteOKConnector(HttpJsonFetcher())  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        RemoteOKConnector(HttpJsonFetcher(), "https://user:secret@remoteok.example.invalid/jobs")
