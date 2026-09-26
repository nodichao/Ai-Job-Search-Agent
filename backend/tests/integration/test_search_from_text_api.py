import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.connectors.base import RawOffer
from app.core.config import Settings
from app.core.errors import SourceUnavailableError
from app.domain.search_preferences import PreferenceStrength, SearchPreferences
from app.domain.user_profile import UserProfile
from app.main import create_app
from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
from app.services.normalization_service import NormalizationService
from app.services.search_pipeline import SearchPipeline
from app.services.search_service import ConnectorBinding, SearchService


FIXTURE = Path(__file__).parents[1] / "fixtures" / "remoteok" / "offer_list.json"


class FakeLLM:
    def __init__(self, preferences=None, error=None):
        self.preferences = preferences or SearchPreferences(
            jobTitles=["Platform Engineer"],
            locations=["Dakar"],
            skills=["Python"],
            preferenceStrength={"jobTitles": PreferenceStrength.REQUIRED},
        )
        self.error = error
        self.calls = []

    async def parse_preferences(self, user_text):
        self.calls.append(user_text)
        if self.error:
            raise self.error
        return self.preferences

    async def extract_profile(self, cv_text):
        raise AssertionError("CV extraction is unrelated to search-from-text")


class RecordingConnector:
    source_name = "RemoteOK"

    def __init__(self, *, fail=False):
        self.criteria = []
        self.fail = fail
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))[0]

    async def search(self, criteria):
        self.criteria.append(criteria)
        if self.fail:
            raise SourceUnavailableError("private connector detail")
        return [RawOffer(
            source_name=self.source_name,
            source_id=str(self.payload["id"]),
            payload=self.payload,
            provenance={"source_url": "https://remoteok.com/api"},
        )]


def _app(tmp_path, llm, connector):
    pipeline = SearchPipeline(
        SearchService([ConnectorBinding(connector)]),
        NormalizationService(),
    )
    runtime = SearchRuntime(
        pipeline=pipeline,
        connectors=(ConnectorAvailability(
            name="RemoteOK", status="development", activeForSearch=True, reason="test connector"
        ),),
    )
    return create_app(
        Settings(database_url=f"sqlite:///{tmp_path / 'settings.db'}"),
        runtime=runtime,
        llm_service=llm,
    )


def test_search_from_text_parses_preferences_uses_profile_and_matches_search_response(tmp_path):
    llm = FakeLLM()
    connector = RecordingConnector()
    profile = {"jobTitles": ["Platform Engineer"], "skills": ["Python"], "totalExperienceYears": 5}
    with TestClient(_app(tmp_path, llm, connector)) as client:
        text_response = client.post("/api/search/from-text", json={
            "profile": profile,
            "preferences_text": "Platform Engineer in Dakar, Python required",
        })
        structured_response = client.post("/api/search", json={
            "profile": profile,
            "preferences": {
                "jobTitles": ["Platform Engineer"], "locations": ["Dakar"], "skills": ["Python"],
                "preferenceStrength": {"jobTitles": "REQUIRED"},
            },
        })

    assert text_response.status_code == structured_response.status_code == 200
    text_body, structured_body = text_response.json(), structured_response.json()
    assert set(text_body) == set(structured_body) == {"results", "matches", "excluded", "ranking", "meta"}
    assert set(text_body["meta"]) == set(structured_body["meta"])
    assert text_body["results"][0]["position"]["title"] == "Senior Platform Engineer"
    assert text_body["matches"][0]["matching"]["dimensions"][-1]["score"] > 0
    assert text_body["matches"][0]["filtering"]["criteria"][0]["strength"] == "REQUIRED"
    assert llm.calls == ["Platform Engineer in Dakar, Python required"]
    assert len(connector.criteria) == 2
    criteria = connector.criteria[0]
    assert criteria.job_titles == ["Platform Engineer"]
    assert criteria.locations == ["Dakar"]
    assert criteria.skills == ["Python"]


def test_search_from_text_rejects_empty_or_invalid_requests_before_llm_and_search(tmp_path):
    llm, connector = FakeLLM(), RecordingConnector()
    with TestClient(_app(tmp_path, llm, connector)) as client:
        missing = client.post("/api/search/from-text", json={"profile": {}})
        empty = client.post("/api/search/from-text", json={"profile": {}, "preferences_text": " \n "})
        oversize = client.post("/api/search/from-text", json={"profile": {}, "preferences_text": "PRIVATE-SEARCH-MARKER" + "x" * 20_001})

    assert [missing.status_code, empty.status_code, oversize.status_code] == [422, 422, 422]
    assert "PRIVATE-SEARCH-MARKER" not in oversize.text
    assert llm.calls == []
    assert connector.criteria == []


def test_preference_parsing_failure_returns_generic_502_and_skips_search(tmp_path):
    llm = FakeLLM(error=RuntimeError("secret provider response and private query"))
    connector = RecordingConnector()
    with TestClient(_app(tmp_path, llm, connector)) as client:
        response = client.post("/api/search/from-text", json={
            "profile": {}, "preferences_text": "PRIVATE-SEARCH-MARKER"
        })
    assert response.status_code == 502
    assert "secret provider response" not in response.text
    assert "PRIVATE-SEARCH-MARKER" not in response.text
    assert connector.criteria == []


def test_from_text_preserves_connector_failure_reporting_and_does_not_persist_settings(tmp_path):
    llm, connector = FakeLLM(), RecordingConnector(fail=True)
    app = _app(tmp_path, llm, connector)
    with TestClient(app) as client:
        saved_profile = client.put("/api/profile", json={"skills": ["Go"]}).json()
        saved_preferences = client.put("/api/preferences", json={"jobTitles": ["SRE"]}).json()
        response = client.post("/api/search/from-text", json={
            "profile": {"jobTitles": ["Platform Engineer"]}, "preferences_text": "Find platform jobs"
        })
        profile_after = client.get("/api/profile").json()
        preferences_after = client.get("/api/preferences").json()

    assert response.status_code == 200
    assert response.json()["meta"]["failedSources"] == [
        {"source": "RemoteOK", "category": "source_unavailable"}
    ]
    assert "private connector detail" not in response.text
    assert profile_after == saved_profile
    assert preferences_after == saved_preferences
