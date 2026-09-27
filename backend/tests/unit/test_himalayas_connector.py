from datetime import datetime, timezone

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.himalayas import HimalayasConnector
from app.core.errors import AuthenticationError, ConnectorError, RateLimitError, SourceUnavailableError
from app.domain.search_criteria import SearchCriteria


FIXTURE = {
    "updatedAt": "2026-09-27T00:00:00Z",
    "limit": 2,
    "totalCount": 3,
    "nextCursor": "opaque-token",
    "jobs": [
        {"guid": "h-1", "title": "Backend Engineer"},
        {"guid": "h-2", "title": "Data Analyst"},
    ],
}


@pytest.mark.asyncio
async def test_connector_preserves_raw_payload_provenance_and_cursor():
    seen = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.url.params))
        payload = FIXTURE if request.url.params.get("cursor") is None else {
            "updatedAt": FIXTURE["updatedAt"], "limit": 2,
            "totalCount": 3, "jobs": [{"guid": "h-3", "title": "Designer"}],
        }
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    connector = HimalayasConnector(
        HttpJsonFetcher(client=client), max_results=3,
        clock=lambda: datetime(2026, 9, 27, tzinfo=timezone.utc),
    )
    offers = await connector.search(SearchCriteria(keywords=["ignored without verified mapping"]))
    await client.aclose()

    assert len(offers) == 3
    assert [offer.source_id for offer in offers] == ["h-1", "h-2", "h-3"]
    assert all(offer.source_name == "Himalayas" for offer in offers)
    assert offers[0].payload == FIXTURE["jobs"][0]
    assert offers[0].retrieved_at == datetime(2026, 9, 27, tzinfo=timezone.utc)
    assert offers[0].provenance["source_url"] == "https://himalayas.app/"
    assert offers[0].provenance["attribution_required"] is True
    assert seen == [{"limit": "3"}, {"limit": "3", "cursor": "opaque-token"}]


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [[], {"jobs": "invalid"}, {"jobs": [None]}])
async def test_connector_rejects_malformed_json_shapes(body):
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
    connector = HimalayasConnector(HttpJsonFetcher(client=client), max_results=5)
    with pytest.raises(ConnectorError):
        await connector.search(SearchCriteria())
    await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(("status", "error"), [(429, RateLimitError), (403, AuthenticationError), (503, SourceUnavailableError)])
async def test_connector_surfaces_http_error_classes_without_rate_limit_retry(status, error):
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    connector = HimalayasConnector(HttpJsonFetcher(client=client), max_results=5)
    with pytest.raises(error):
        await connector.search(SearchCriteria())
    await client.aclose()
    assert calls == (3 if status == 503 else 1)
