import json
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.core.config import Settings
from app.main import create_app
from app.services.connector_runtime import build_search_runtime

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.asyncio
async def test_api_composes_two_fixture_connectors_and_returns_canonical_job_offers():
    requests = []
    remoteok = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    lever = json.loads((FIXTURES / "lever" / "page_one.json").read_text(encoding="utf-8"))

    def source_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api":
            return httpx.Response(200, json=remoteok)
        if request.url.path == "/v0/postings/company-board":
            return httpx.Response(200, json=lever)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(source_handler)) as source_client:
        runtime = build_search_runtime(
            Settings(
                remoteok_enabled=True,
                remoteok_endpoint="https://remoteok.example.test/api",
                lever_enabled=True,
                lever_site="company-board",
                recommendation_minimum_confidence=0.3,
            ),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        assert requests == []  # Composition itself must not trigger HTTP.
        app = create_app(runtime=runtime)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as api_client:
            response = await api_client.post("/api/search", json={
                "profile": {"jobTitles": ["Platform Engineer"]},
                "preferences": {"jobTitles": ["Engineer"], "skills": ["Python"]},
            })

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 3
    assert body["meta"]["sources"] == ["RemoteOK", "Lever"]
    assert body["meta"]["failedSources"] == []
    assert {offer["source"]["name"] for offer in body["results"]} == {"RemoteOK", "Lever"}
    assert all("payload" not in offer and "provenance" not in offer for offer in body["results"])
    assert body["results"][0]["position"]["title"] == "Senior Platform Engineer"
    assert body["results"][1]["position"]["title"] == "Platform Engineer"
    assert len(body["matches"]) == 3
    assert {item["recommendation"]["decision"] for item in body["matches"]} == {
        "RECOMMENDED", "NOT_RECOMMENDED"
    }
    assert body["ranking"]["total"] == 2
    assert [item["offer"]["position"]["title"] for item in body["ranking"]["offers"]] == [
        "Platform Engineer", "Senior Platform Engineer"
    ]
    assert all("matching" not in offer and "recommendation" not in offer for offer in body["results"])
    assert len(requests) == 2
    assert requests[0].url.query == b""


class StubConnector:
    def __init__(self, source_name: str, *, fail: bool = False, offers=None):
        from app.core.errors import SourceUnavailableError
        from app.connectors.base import RawOffer

        self.source_name = source_name
        self.fail = fail
        self._error = SourceUnavailableError
        self.offers = offers if offers is not None else [RawOffer(source_name=source_name, payload={})]

    async def search(self, criteria):
        if self.fail:
            raise self._error("private internal detail")
        return self.offers


@pytest.mark.asyncio
async def test_api_reports_one_source_failure_and_keeps_successful_source_results():
    from app.connectors.base import RawOffer
    from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
    from app.services.normalization_service import NormalizationService
    from app.services.search_pipeline import SearchPipeline
    from app.services.search_service import ConnectorBinding, SearchService

    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))[0]
    good = StubConnector("RemoteOK", offers=[RawOffer(source_name="RemoteOK", source_id=str(fixture["id"]), payload=fixture,
        provenance={"source_url": "https://remoteok.com/"})])
    bad = StubConnector("Lever", fail=True)
    runtime = SearchRuntime(
        pipeline=SearchPipeline(SearchService([ConnectorBinding(bad), ConnectorBinding(good)]), NormalizationService()),
        connectors=(ConnectorAvailability(name="RemoteOK", status="development", activeForSearch=True, reason="test"),),
    )
    app = create_app(runtime=runtime)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1
    assert response.json()["meta"]["failedSources"] == [{"source": "Lever", "category": "source_unavailable"}]
    assert "private internal detail" not in response.text


@pytest.mark.asyncio
async def test_api_reports_all_sources_failed_without_exposing_internal_errors():
    from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
    from app.services.normalization_service import NormalizationService
    from app.services.search_pipeline import SearchPipeline
    from app.services.search_service import ConnectorBinding, SearchService

    runtime = SearchRuntime(
        pipeline=SearchPipeline(
            SearchService([ConnectorBinding(StubConnector("RemoteOK", fail=True)), ConnectorBinding(StubConnector("Lever", fail=True))]),
            NormalizationService(),
        ),
        connectors=(
            ConnectorAvailability(name="RemoteOK", status="development", activeForSearch=True, reason="test"),
            ConnectorAvailability(name="Lever", status="access pending", activeForSearch=True, reason="test"),
        ),
    )
    app = create_app(runtime=runtime)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert {item["category"] for item in response.json()["meta"]["failedSources"]} == {"source_unavailable"}
    assert "private internal detail" not in response.text


@pytest.mark.asyncio
async def test_api_with_one_enabled_connector_returns_normalized_results():
    remoteok = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=remoteok)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api"),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as api_client:
            response = await api_client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 200
    assert calls == 1
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["meta"]["sources"] == ["RemoteOK"]
    assert body["meta"]["failedSources"] == []
    assert body["results"][0]["position"]["title"] == "Senior Platform Engineer"


@pytest.mark.asyncio
async def test_configured_source_with_no_offers_is_distinct_from_source_failure():
    from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
    from app.services.normalization_service import NormalizationService
    from app.services.search_pipeline import SearchPipeline
    from app.services.search_service import ConnectorBinding, SearchService

    empty = StubConnector("RemoteOK", offers=[])
    runtime = SearchRuntime(
        pipeline=SearchPipeline(SearchService([ConnectorBinding(empty)]), NormalizationService()),
        connectors=(ConnectorAvailability(name="RemoteOK", status="development", activeForSearch=True, reason="test"),),
    )
    app = create_app(runtime=runtime)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert response.json()["meta"]["failedSources"] == []


@pytest.mark.asyncio
async def test_api_returns_filtered_canonical_offers_and_separate_match_explanations():
    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=fixture)
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api"),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/search", json={
                "profile": {"skills": ["Python"], "jobTitles": ["Platform Engineer"], "totalExperienceYears": 8},
                "preferences": {"jobTitles": ["Engineer"]},
            })

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["position"]["title"] == "Senior Platform Engineer"
    assert body["results"][0]["source"]["name"] == "RemoteOK"
    assert body["results"][0]["source"]["retrievedAt"]
    assert len(body["matches"]) == 1
    match = body["matches"][0]
    assert match["offerIdentity"]["sourceId"] == "735421"
    assert match["matching"]["score"] is not None
    assert match["explanation"]["score"] == match["matching"]["score"]
    assert match["recommendation"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert body["ranking"]["total"] == 0
    assert "matchScore" not in body["results"][0]
    assert "matching" not in body["results"][0]
    assert body["excluded"] == []


@pytest.mark.asyncio
async def test_api_excludes_known_required_conflict_but_keeps_structured_explanation():
    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=fixture)
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api"),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/search", json={
                "profile": {},
                "preferences": {
                    "jobTitles": ["Designer"],
                    "preferenceStrength": {"jobTitles": "REQUIRED"},
                },
            })

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["matches"] == []
    assert len(body["excluded"]) == 1
    assert body["excluded"][0]["offer"]["position"]["title"] == "Senior Platform Engineer"
    assert body["excluded"][0]["filtering"]["included"] is False
    assert body["excluded"][0]["filtering"]["conflicts"] == ["jobTitles"]
    assert body["excluded"][0]["recommendation"]["decision"] == "NOT_RECOMMENDED"
