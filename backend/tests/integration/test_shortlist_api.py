import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.connectors.common.http import HttpJsonFetcher
from app.core.config import Settings
from app.main import create_app


FIXTURES = Path(__file__).parents[1] / "fixtures"


def _database_url(path: Path) -> str:
    return f"sqlite:///{path}"


def _offer_payload(source_id: str | None = "remote-1") -> dict:
    return {
        "identity": {"sourceId": source_id, "offerUrl": "https://jobs.example/remote-1", "slug": "remote-1"},
        "source": {"name": "RemoteOK", "url": "https://remoteok.example/", "retrievedAt": "2026-09-26T12:00:00Z"},
        "position": {"title": "Platform Engineer", "sourceSummary": "Source text"},
        "company": {"name": "ExampleCo"},
        "application": {"applyUrl": "https://apply.example/remote-1"},
    }


def test_shortlist_api_crud_status_validation_duplicate_and_missing_entries(tmp_path):
    app = create_app(Settings(database_url=_database_url(tmp_path / "shortlist.db")))
    with TestClient(app) as client:
        added = client.post("/api/shortlist", json=_offer_payload())
        assert added.status_code == 201
        entry = added.json()
        entry_id = entry["id"]
        assert entry["status"] == "SAVED"
        assert entry["offer"]["identity"]["sourceId"] == "remote-1"
        assert entry["offer"]["source"]["name"] == "RemoteOK"
        assert entry["offer"]["source"]["retrievedAt"] == "2026-09-26T12:00:00Z"

        duplicate = client.post("/api/shortlist", json=_offer_payload())
        assert duplicate.status_code == 409

        listed = client.get("/api/shortlist")
        assert listed.status_code == 200 and len(listed.json()) == 1
        assert client.get(f"/api/shortlist/{entry_id}").json() == entry
        assert client.get("/api/shortlist/missing").status_code == 404

        for status in ("SAVED", "INTERESTED", "APPLYING", "APPLIED", "REJECTED", "ARCHIVED"):
            updated = client.patch(f"/api/shortlist/{entry_id}", json={"status": status})
            assert updated.status_code == 200
            assert updated.json()["status"] == status
        assert client.patch(f"/api/shortlist/{entry_id}", json={"status": "SUBMITTED"}).status_code == 422
        assert client.patch("/api/shortlist/missing", json={"status": "APPLIED"}).status_code == 404

        deleted = client.delete(f"/api/shortlist/{entry_id}")
        assert deleted.status_code == 204
        assert client.delete(f"/api/shortlist/{entry_id}").status_code == 404
        assert client.get("/api/shortlist").json() == []


def test_shortlist_rejects_offer_without_stable_identity(tmp_path):
    app = create_app(Settings(database_url=_database_url(tmp_path / "shortlist.db")))
    payload = _offer_payload(source_id=None)
    payload["identity"].update({"id": None, "slug": None, "offerUrl": None})
    with TestClient(app) as client:
        response = client.post("/api/shortlist", json=payload)
    assert response.status_code == 422
    assert "stable" in response.text.lower() or "source ID" in response.text


@pytest.mark.asyncio
async def test_nonrecommended_search_offer_can_be_saved_and_survives_app_recreation(tmp_path):
    database_url = _database_url(tmp_path / "persistent-shortlist.db")
    fixture = json.loads((FIXTURES / "remoteok" / "offer_list.json").read_text(encoding="utf-8"))
    request_count = 0

    def source_handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json=fixture)

    async with httpx.AsyncClient(transport=httpx.MockTransport(source_handler)) as source_client:
        settings = Settings(
            database_url=database_url,
            remoteok_enabled=True,
            remoteok_endpoint="https://remoteok.example.test/api",
            himalayas_enabled=False,
            recommendation_minimum_confidence=0.3,
        )
        app = create_app(settings, fetcher=HttpJsonFetcher(client=source_client))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            search_request = {
                "profile": {"jobTitles": ["Accountant"]},
                "preferences": {"jobTitles": ["Designer"]},
            }
            first_search = await client.post("/api/search", json=search_request)
            assert first_search.status_code == 200
            assert len(first_search.json()["results"]) == 1
            assert first_search.json()["matches"][0]["recommendation"]["decision"] == "NOT_RECOMMENDED"
            offer = first_search.json()["results"][0]

            saved = await client.post("/api/shortlist", json=offer)
            assert saved.status_code == 201
            assert saved.json()["status"] == "SAVED"
            assert saved.json()["offer"]["identity"]["sourceId"] == offer["identity"]["sourceId"]

            second_search = await client.post("/api/search", json=search_request)
            assert second_search.status_code == 200
            assert second_search.json()["matches"][0]["matching"] == first_search.json()["matches"][0]["matching"]
            assert second_search.json()["matches"][0]["recommendation"] == first_search.json()["matches"][0]["recommendation"]
            assert second_search.json()["ranking"] == first_search.json()["ranking"]
            assert request_count == 2

    recreated = create_app(Settings(database_url=database_url))
    with TestClient(recreated) as client:
        listed = client.get("/api/shortlist")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["offer"]["identity"]["sourceId"] == offer["identity"]["sourceId"]
    assert listed.json()[0]["offer"]["source"]["url"] == offer["source"]["url"]


def test_storage_failure_returns_safe_service_unavailable_response(tmp_path):
    unusable_path = tmp_path / "directory-not-a-db"
    unusable_path.mkdir()
    app = create_app(Settings(database_url=_database_url(unusable_path)))
    with TestClient(app) as client:
        response = client.get("/api/shortlist")
    assert response.status_code == 503
    assert str(tmp_path) not in response.text
