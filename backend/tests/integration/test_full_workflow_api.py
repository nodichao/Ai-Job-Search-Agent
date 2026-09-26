import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.connectors.base import RawOffer
from app.core.config import Settings
from app.main import create_app
from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
from app.services.normalization_service import NormalizationService
from app.services.search_pipeline import SearchPipeline
from app.services.search_service import ConnectorBinding, SearchService

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FixtureConnector:
    source_name = "RemoteOK"

    def __init__(self) -> None:
        payload = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))[0]
        self.offer = RawOffer(
            source_name=self.source_name,
            source_id=str(payload["id"]),
            payload=payload,
            provenance={"source_url": "https://remoteok.com/"},
        )

    async def search(self, criteria):
        return [self.offer]


def _app(database_path: Path):
    connector = FixtureConnector()
    runtime = SearchRuntime(
        pipeline=SearchPipeline(
            SearchService([ConnectorBinding(connector)]),
            NormalizationService(),
        ),
        connectors=(ConnectorAvailability(
            name="RemoteOK",
            status="development",
            activeForSearch=True,
            reason="deterministic fixture connector",
        ),),
    )
    return create_app(Settings(database_url=f"sqlite:///{database_path}"), runtime=runtime)


def test_complete_profile_to_search_shortlist_http_workflow_and_restart(tmp_path):
    database = tmp_path / "workflow.db"
    with TestClient(_app(database)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/profile").status_code == 404
        assert client.get("/api/preferences").status_code == 404

        profile = {"skills": ["Python"], "jobTitles": ["Platform Engineer"]}
        prefs = {
            "jobTitles": ["Engineer"],
            "locations": ["Dakar"],
            "salary": {"minimum": 1000, "currency": "USD"},
            "preferenceStrength": {"locations": "PREFERRED"},
        }
        assert client.put("/api/profile", json=profile).status_code == 200
        assert client.get("/api/profile").json()["skills"] == ["Python"]
        assert client.patch("/api/profile", json={"skills": ["Python", "SQL"]}).status_code == 200
        assert client.put("/api/preferences", json=prefs).status_code == 200
        assert client.get("/api/preferences").json()["salary"]["minimum"] == 1000
        patched_prefs = client.patch("/api/preferences", json={"salary": {"maximum": 5000}})
        assert patched_prefs.status_code == 200
        assert patched_prefs.json()["salary"] == {
            "minimum": 1000, "maximum": 5000, "currency": "USD", "period": None
        }
        assert client.get("/api/profile").json()["skills"] == ["Python", "SQL"]

        search_response = client.post("/api/search", json={
            "profile": client.get("/api/profile").json(),
            "preferences": client.get("/api/preferences").json(),
        })
        assert search_response.status_code == 200
        search_body = search_response.json()
        assert {"results", "matches", "excluded", "ranking", "meta"} <= set(search_body)
        assert search_body["meta"]["total"] == 1
        offer = search_body["results"][0]
        assert offer["source"]["name"] == "RemoteOK"
        assert offer["identity"]["sourceId"] == "735421"
        assert offer["position"]["title"] == "Senior Platform Engineer"
        assert "payload" not in offer and "provenance" not in offer
        assert "matching" not in offer and "recommendation" not in offer

        saved_response = client.post("/api/shortlist", json=offer)
        assert saved_response.status_code == 201
        entry = saved_response.json()
        entry_id = entry["id"]
        assert entry["offer"] == offer
        assert "matching" not in entry["offer"] and "recommendation" not in entry["offer"]
        assert client.get(f"/api/shortlist/{entry_id}").json() == entry
        listed = client.get("/api/shortlist")
        assert listed.status_code == 200 and len(listed.json()) == 1
        assert client.post("/api/shortlist", json=offer).status_code == 409
        assert client.post("/api/shortlist", json={"unknown": True}).status_code == 422
        updated = client.patch(f"/api/shortlist/{entry_id}", json={"status": "INTERESTED"})
        assert updated.status_code == 200 and updated.json()["status"] == "INTERESTED"
        assert client.delete(f"/api/shortlist/{entry_id}").status_code == 204
        assert client.get(f"/api/shortlist/{entry_id}").status_code == 404

        assert client.post("/api/search", json={}).status_code == 422

    with TestClient(_app(database)) as recreated:
        assert recreated.get("/api/profile").json()["skills"] == ["Python", "SQL"]
        assert recreated.get("/api/preferences").json()["salary"]["maximum"] == 5000
        assert recreated.get("/api/shortlist").json() == []


def test_postman_collection_is_valid_and_covers_the_local_workflow():
    collection_path = Path(__file__).parents[2] / "postman" / "AI-Job-Search-Agent.postman_collection.json"
    collection = json.loads(collection_path.read_text(encoding="utf-8"))
    request_urls = [item["request"]["url"] for item in collection["item"]]
    variables = {item["key"]: item["value"] for item in collection["variable"]}

    assert collection["info"]["schema"].endswith("collection/v2.1.0/collection.json")
    assert variables["baseUrl"] == "http://localhost:8000"
    assert "shortlistId" in variables
    assert "{{baseUrl}}/health" in request_urls
    assert all(f"{{{{baseUrl}}}}{path}" in request_urls for path in (
        "/api/profile", "/api/preferences", "/api/search", "/api/shortlist"
    ))
    assert any("{{shortlistId}}" in url for url in request_urls)
