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
                himalayas_enabled=False,
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
    assert body["ranking"]["total"] == 1
    assert [item["offer"]["position"]["title"] for item in body["ranking"]["offers"]] == [
        "Platform Engineer"
    ]
    assert all("matching" not in offer and "recommendation" not in offer for offer in body["results"])
    assert len(requests) == 2
    assert requests[0].url.query == b""


@pytest.mark.asyncio
async def test_api_combines_himalayas_and_remoteok_and_isolates_one_source_error():
    remoteok = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    requests = []

    def source_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "remoteok.example.test":
            return httpx.Response(503)
        if request.url.host == "himalayas.app":
            return httpx.Response(200, json={
                "updatedAt": "2026-09-27T00:00:00Z",
                "limit": 20,
                "totalCount": 1,
                "jobs": [{
                    "guid": "h-test-1", "title": "Platform Engineer",
                    "companyName": "Example", "description": "Operate platforms",
                    "applicationLink": "https://example.test/apply",
                    "categories": ["Engineering"],
                }],
            })
        if request.url.path == "/api":
            return httpx.Response(200, json=remoteok)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(source_handler)) as source_client:
        runtime = build_search_runtime(
            Settings(
                remoteok_enabled=True,
                remoteok_endpoint="https://remoteok.example.test/api",
                himalayas_enabled=True,
                lever_enabled=False,
            ),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        app = create_app(runtime=runtime)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as api_client:
            response = await api_client.post("/api/search", json={
                "profile": {"jobTitles": ["Platform Engineer"]},
                "preferences": {"jobTitles": ["Engineer"]},
            })

    assert response.status_code == 200
    body = response.json()
    assert len(requests) == 4  # Himalayas once; RemoteOK uses the shared 3-attempt transient retry policy.
    assert {request.url.host for request in requests} == {"himalayas.app", "remoteok.example.test"}
    assert body["meta"]["sources"] == ["Himalayas"]
    assert body["meta"]["failedSources"] == [{"source": "RemoteOK", "category": "source_unavailable"}]
    assert body["results"][0]["source"]["name"] == "Himalayas"
    assert body["results"][0]["identity"]["sourceId"] == "h-test-1"
    assert "payload" not in body["results"][0]
    assert body["meta"]["normalizationFailures"]["totalRejected"] == 0


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
    assert response.json()["meta"]["normalizationFailures"] == {"totalRejected": 0, "bySource": []}
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
    feed_body = [{
        "last_updated": 1790438426,
        "legal": "Credit Remote OK as source and link the original job URL.",
    }, *remoteok]
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=feed_body)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
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
    assert body["meta"]["normalizationFailures"] == {"totalRejected": 0, "bySource": []}
    assert body["results"][0]["position"]["title"] == "Senior Platform Engineer"


@pytest.mark.asyncio
async def test_api_reports_per_source_normalization_rejections_and_keeps_valid_offers():
    valid = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))[0]
    malformed = [
        {"id": 810001, "company": "Missing title"},
        {"id": 810002, "position": "   ", "company": "Blank title"},
    ]
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=[valid, *malformed])
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/search", json={"profile": {}, "preferences": {}})

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert [item["identity"]["sourceId"] for item in body["results"]] == [str(valid["id"])]
    assert len(body["matches"]) == 1
    assert body["meta"]["normalizationFailures"] == {
        "totalRejected": 2,
        "bySource": [{"source": "RemoteOK", "rejected": 2}],
    }
    assert body["meta"]["failedSources"] == []


@pytest.mark.asyncio
async def test_pipeline_deduplicates_normalized_offers_before_filtering_and_api_output():
    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))[0]
    duplicate = {**fixture, "id": fixture["id"] + 1}
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=[fixture, duplicate])
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/search", json={"profile": {}, "preferences": {}})

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert len(body["matches"]) + len(body["excluded"]) == 1
    assert body["results"][0]["identity"]["sourceId"] == str(fixture["id"])


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
    assert response.json()["meta"]["normalizationFailures"] == {"totalRejected": 0, "bySource": []}


@pytest.mark.asyncio
async def test_api_returns_filtered_canonical_offers_and_separate_match_explanations():
    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=fixture)
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
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
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
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
    assert "matching" in body["excluded"][0]
    assert "explanation" in body["excluded"][0]
    assert body["excluded"][0]["matching"]["score"] is not None
    assert body["excluded"][0]["explanation"]["score"] == body["excluded"][0]["matching"]["score"]
    assert body["excluded"][0]["recommendation"]["decision"] == "NOT_RECOMMENDED"
    assert body["ranking"] == {"offers": [], "total": 0}


@pytest.mark.asyncio
async def test_api_serializes_partial_title_overlap_consistently_without_excluding_preferred_offers():
    fixture = [
        {"id": 820001, "position": "DESARROLLADOR FULL STACK"},
        {"id": 820002, "position": "Frontend Developer"},
    ]
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=fixture)
    )) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/search", json={
                "profile": {"jobTitles": ["Full-Stack Developer"]},
                "preferences": {
                    "jobTitles": ["Full-Stack Developer"],
                    "preferenceStrength": {"jobTitles": "PREFERRED"},
                },
            })

    assert response.status_code == 200
    body = response.json()
    assert {item["identity"]["sourceId"] for item in body["results"]} == {"820001", "820002"}
    assert body["excluded"] == []
    assert body["meta"]["normalizationFailures"] == {"totalRejected": 0, "bySource": []}
    for match in body["matches"]:
        filtering_title = next(item for item in match["filtering"]["criteria"] if item["name"] == "jobTitles")
        preference_dimension = next(item for item in match["matching"]["dimensions"] if item["name"] == "preferences")
        assert filtering_title["status"] == "UNKNOWN"
        assert filtering_title["strength"] == "PREFERRED"
        assert preference_dimension["status"] == "UNKNOWN"
        assert match["recommendation"]["decision"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.asyncio
async def test_remoteok_poc_profile_preferences_flow_through_filtering_and_ranking():
    fixture = json.loads((FIXTURES / "remoteok" / "poc_scenario.json").read_text(encoding="utf-8"))
    source_requests = 0

    def source_handler(request: httpx.Request) -> httpx.Response:
        nonlocal source_requests
        source_requests += 1
        return httpx.Response(200, json=fixture)

    profile = {
        "skills": ["React", "Node.js", "MongoDB"],
        "jobTitles": ["Full-Stack Developer"],
        "experience": ["Développeur MERN"],
        "totalExperienceYears": 2,
        "education": ["Licence en Génie Logiciel"],
        "languages": ["Français", "Anglais"],
        "domains": ["Web Development"],
        "rawSourceMetadata": {},
    }
    preferences = {
        "jobTitles": ["Full-Stack Developer", "Frontend Developer"],
        "locations": ["Dakar"],
        "countries": ["Senegal"],
        "remote": True,
        "seniority": ["JUNIOR", "MID"],
        "employmentTypes": ["FULL_TIME"],
        "skills": ["React", "Node.js", "MongoDB"],
        "salary": {
            "minimum": 500000,
            "maximum": 1000000,
            "currency": "XOF",
            "period": "MONTH",
        },
        "companies": [],
        "timezone": "Africa/Dakar",
        "preferenceStrength": {
            "locations": "REQUIRED",
            "skills": "PREFERRED",
            "salary": "OPTIONAL",
        },
    }

    async with httpx.AsyncClient(transport=httpx.MockTransport(source_handler)) as source_client:
        app = create_app(
            Settings(remoteok_enabled=True, remoteok_endpoint="https://remoteok.example.test/api", himalayas_enabled=False),
            fetcher=HttpJsonFetcher(client=source_client),
        )
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as api_client:
            first = await api_client.post("/api/search", json={"profile": profile, "preferences": preferences})
            second = await api_client.post("/api/search", json={"profile": profile, "preferences": preferences})

    assert first.status_code == second.status_code == 200
    body = first.json()
    repeated = second.json()
    assert source_requests == 2
    assert body["meta"]["total"] == 2  # One exact source-id duplicate was removed.
    assert body["meta"]["sources"] == ["RemoteOK"]
    assert body["meta"]["failedSources"] == []
    remote_status = next(item for item in body["meta"]["connectors"] if item["name"] == "RemoteOK")
    assert remote_status["activeForSearch"] is True
    assert remote_status["status"] == "development"

    included = {item["identity"]["sourceId"]: item for item in body["results"]}
    assert set(included) == {"900001", "900003"}
    matches = {item["offerIdentity"]["sourceId"]: item for item in body["matches"]}
    assert set(matches) == set(included)
    assert included["900001"]["position"]["title"] == "Full-Stack Developer"
    assert included["900001"]["position"]["description"] == "Build web products with React and Node.js."
    assert included["900001"]["position"]["skills"] == []
    assert included["900001"]["position"]["categories"] == ["React", "Node.js", "MongoDB"]
    assert included["900001"]["location"]["remote"] is None
    assert included["900001"]["compensation"]["components"][0]["currency"] is None
    assert included["900001"]["compensation"]["components"][0]["period"] is None

    assert len(body["matches"]) == len(body["results"]) == 2
    scored = matches["900001"]
    assert scored["matching"]["score"] == repeated["matches"][0]["matching"]["score"]
    assert scored["matching"]["score"] == 100
    assert scored["matching"]["confidence"] == 0.35
    assert scored["matching"]["confidence"] < 0.5
    assert scored["recommendation"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert scored["recommendation"]["reasons"][0]["code"] == "CONFIDENCE_TOO_LOW"
    dimensions = {item["name"]: item for item in scored["matching"]["dimensions"]}
    assert set(dimensions) == {"skills", "preferences", "experience", "roleAlignment"}
    assert dimensions["skills"]["status"] == "UNKNOWN"
    assert dimensions["skills"]["score"] is None
    assert dimensions["preferences"]["status"] == "UNKNOWN"
    assert dimensions["preferences"]["score"] == 100
    assert dimensions["experience"]["status"] == "UNKNOWN"
    assert dimensions["experience"]["score"] is None
    assert dimensions["roleAlignment"]["status"] == "SATISFIED"
    assert dimensions["roleAlignment"]["score"] == 100
    assert scored["explanation"]["score"] == scored["matching"]["score"]
    assert scored["explanation"]["confidence"] == scored["matching"]["confidence"]
    assert scored["explanation"]["dimensions"] == scored["matching"]["dimensions"]
    assert set(scored["filtering"]["unknownCriteria"]) >= {
        "countries", "remote", "seniority", "employmentTypes", "skills", "timezone", "salary"
    }

    missing = matches["900003"]
    assert included["900003"]["location"]["locations"] == []
    assert included["900003"]["location"]["cities"] == []
    assert included["900003"]["location"]["countries"] == []
    assert missing["filtering"]["included"] is True
    assert {"locations", "countries", "remote", "salary"}.issubset(missing["filtering"]["unknownCriteria"])
    missing_dimensions = {item["name"]: item for item in missing["matching"]["dimensions"]}
    assert missing_dimensions["skills"]["status"] == "UNKNOWN"
    assert missing_dimensions["skills"]["score"] is None
    assert missing_dimensions["experience"]["status"] == "UNKNOWN"
    assert missing_dimensions["experience"]["score"] is None
    assert missing["recommendation"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert missing["matching"]["confidence"] == 0.35

    assert len(body["excluded"]) == 1
    excluded = body["excluded"][0]
    assert excluded["offer"]["identity"]["sourceId"] == "900002"
    assert excluded["filtering"]["included"] is False
    assert excluded["filtering"]["conflicts"] == ["locations"]
    assert excluded["recommendation"]["decision"] == "NOT_RECOMMENDED"
    required_location = next(item for item in excluded["filtering"]["criteria"] if item["name"] == "locations")
    assert required_location["strength"] == "REQUIRED"
    assert required_location["status"] == "CONFLICT"
    assert excluded["offer"]["identity"]["sourceId"] not in matches

    # Ranking is a subset of API results whose serialized recommendation is RECOMMENDED.
    ranking_ids = {item["offer"]["identity"]["sourceId"] for item in body["ranking"]["offers"]}
    recommended_ids = {
        source_id for source_id, item in matches.items()
        if item["recommendation"]["decision"] == "RECOMMENDED"
    }
    assert ranking_ids == recommended_ids == set()
    assert body["ranking"] == {"offers": [], "total": 0}


@pytest.mark.asyncio
async def test_remoteok_failure_is_reported_without_discarding_other_source_results():
    from app.connectors.base import RawOffer
    from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
    from app.services.normalization_service import NormalizationService
    from app.services.search_pipeline import SearchPipeline
    from app.services.search_service import ConnectorBinding, SearchService

    lever_record = json.loads((FIXTURES / "lever" / "page_one.json").read_text(encoding="utf-8"))[0]
    remoteok = StubConnector("RemoteOK", fail=True, offers=[])
    lever = StubConnector("Lever", offers=[RawOffer(
        source_name="Lever",
        source_id=lever_record["id"],
        payload=lever_record,
        provenance={"company_name": "Fixture employer"},
    )])
    runtime = SearchRuntime(
        pipeline=SearchPipeline(
            SearchService([ConnectorBinding(remoteok), ConnectorBinding(lever)]),
            NormalizationService(),
        ),
        connectors=(
            ConnectorAvailability(name="RemoteOK", status="development", activeForSearch=True, reason="fixture"),
            ConnectorAvailability(name="Lever", status="access pending", activeForSearch=True, reason="fixture"),
        ),
    )
    app = create_app(runtime=runtime)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/search", json={"profile": {}, "preferences": {}})

    assert response.status_code == 200
    body = response.json()
    assert [offer["source"]["name"] for offer in body["results"]] == ["Lever"]
    assert body["meta"]["failedSources"] == [{"source": "RemoteOK", "category": "source_unavailable"}]
