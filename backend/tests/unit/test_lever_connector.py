import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.retry import RetryPolicy
from app.connectors.lever import LeverConnector, LeverSiteContext
from app.core.errors import AuthenticationError, ConnectorError, RateLimitError, SourceUnavailableError
from app.domain.search_criteria import SearchCriteria

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "lever"
NOW = datetime(2026, 9, 26, 10, tzinfo=timezone.utc)


def fixture(name: str):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_site_scoped_pages_create_raw_offers_and_preserve_provenance():
    requests = []

    def handler(request):
        requests.append(request)
        skip = int(request.url.params["skip"])
        body = fixture("page_one.json") if skip == 0 else fixture("page_two.json")
        return httpx.Response(200, json=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = LeverConnector(HttpJsonFetcher(client=client), LeverSiteContext("example-board", "Example"), page_size=2, clock=lambda: NOW)
        raw = await connector.search(SearchCriteria(keywords=["not a supported source query"]))

    assert [offer.source_id for offer in raw] == ["lever-101", "lever-102", "lever-103"]
    assert raw[0].source_name == "Lever"
    assert raw[0].payload == fixture("page_one.json")[0]
    assert raw[0].retrieved_at == NOW
    assert raw[0].provenance == {
        "format": "json", "request_url": "https://api.lever.co/v0/postings/example-board",
        "site": "example-board", "company_name": "Example", "skip": 0, "limit": 2,
    }
    assert len(requests) == 2
    assert requests[0].url.path == "/v0/postings/example-board"
    assert dict(requests[0].url.params) == {"skip": "0", "limit": "2", "mode": "json"}
    assert requests[1].url.params["skip"] == "2"


@pytest.mark.asyncio
async def test_page_size_and_result_cap_bound_pagination():
    calls = []
    body = fixture("page_one.json") + fixture("page_two.json")

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = LeverConnector(HttpJsonFetcher(client=client), LeverSiteContext("board"), page_size=2, max_results=3)
        raw = await connector.search(SearchCriteria())
    assert len(raw) == 3
    assert [request.url.params["skip"] for request in calls] == ["0", "2"]
    assert [request.url.params["limit"] for request in calls] == ["2", "1"]


@pytest.mark.asyncio
async def test_invalid_response_shapes_are_rejected():
    for body in ({"postings": []}, ["not an object"]):
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))) as client:
            with pytest.raises(ConnectorError):
                await LeverConnector(HttpJsonFetcher(client=client), LeverSiteContext("board")).search(SearchCriteria())


@pytest.mark.asyncio
async def test_timeout_is_reported_as_transient_source_unavailability():
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpJsonFetcher(client=client, retry_policy=RetryPolicy(max_attempts=1))
        with pytest.raises(SourceUnavailableError):
            await LeverConnector(fetcher, LeverSiteContext("board")).search(SearchCriteria())


@pytest.mark.asyncio
@pytest.mark.parametrize(("status", "error"), [(401, AuthenticationError), (403, AuthenticationError), (429, RateLimitError), (404, ConnectorError)])
async def test_authorization_rate_limit_and_http_errors_are_not_retried(status, error):
    calls = 0
    def handler(_):
        nonlocal calls
        calls += 1
        return httpx.Response(status)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(error):
            await LeverConnector(HttpJsonFetcher(client=client), LeverSiteContext("board")).search(SearchCriteria())
    assert calls == 1


def test_explicit_site_is_required():
    for site in ("", "  ", ".", ".."):
        with pytest.raises(ValueError):
            LeverSiteContext(site)
