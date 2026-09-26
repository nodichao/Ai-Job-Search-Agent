from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _database_url(path: Path) -> str:
    return f"sqlite:///{path}"


def test_profile_and_preferences_crud_patch_isolation_and_restart(tmp_path):
    database_url = _database_url(tmp_path / "settings.db")
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        assert client.get("/api/profile").status_code == 404
        assert client.get("/api/preferences").status_code == 404

        profile = {"skills": ["Python"], "jobTitles": ["Backend Engineer"]}
        preferences = {
            "jobTitles": ["Platform Engineer"],
            "locations": ["Dakar"],
            "salary": {"minimum": 1200, "currency": "USD"},
            "preferenceStrength": {"locations": "REQUIRED"},
        }
        assert client.put("/api/profile", json=profile).json()["jobTitles"] == profile["jobTitles"]
        assert client.put("/api/preferences", json=preferences).json()["salary"]["minimum"] == 1200

        changed_profile = client.patch("/api/profile", json={"skills": ["Python", "SQL"]})
        assert changed_profile.status_code == 200
        assert changed_profile.json()["jobTitles"] == ["Backend Engineer"]
        assert changed_profile.json()["skills"] == ["Python", "SQL"]
        assert client.get("/api/preferences").json()["locations"] == ["Dakar"]

        changed_preferences = client.patch("/api/preferences", json={"locations": ["Senegal"]})
        assert changed_preferences.status_code == 200
        assert changed_preferences.json()["jobTitles"] == ["Platform Engineer"]
        assert client.get("/api/profile").json()["skills"] == ["Python", "SQL"]
        salary_patch = client.patch("/api/preferences", json={"salary": {"maximum": 5000}})
        assert salary_patch.status_code == 200
        assert salary_patch.json()["salary"] == {"minimum": 1200, "maximum": 5000, "currency": "USD", "period": None}
        strength_patch = client.patch("/api/preferences", json={"preferenceStrength": {"skills": "PREFERRED"}})
        assert strength_patch.status_code == 200
        assert strength_patch.json()["preferenceStrength"] == {"locations": "REQUIRED", "skills": "PREFERRED"}

        replacement = client.put("/api/profile", json={"skills": ["Go"]})
        assert replacement.status_code == 200
        assert replacement.json()["jobTitles"] == []
        assert client.get("/api/preferences").json()["locations"] == ["Senegal"]

    with TestClient(create_app(Settings(database_url=database_url))) as client:
        assert client.get("/api/profile").json()["skills"] == ["Go"]
        assert client.get("/api/preferences").json()["locations"] == ["Senegal"]


def test_profile_and_preferences_validation_and_missing_patch(tmp_path):
    with TestClient(create_app(Settings(database_url=_database_url(tmp_path / "validation.db")))) as client:
        assert client.patch("/api/profile", json={"skills": ["x"]}).status_code == 404
        assert client.patch("/api/preferences", json={"locations": ["x"]}).status_code == 404
        assert client.put("/api/profile", json={"totalExperienceYears": -1}).status_code == 422
        assert client.put("/api/profile", json={"unknown": "value"}).status_code == 422
        assert client.put("/api/preferences", json={"salary": {"minimum": -1}}).status_code == 422
        assert client.put("/api/preferences", json={"unknown": "value"}).status_code == 422

        assert client.put("/api/profile", json={}).status_code == 200
        assert client.put("/api/preferences", json={}).status_code == 200
        assert client.patch("/api/profile", json={"totalExperienceYears": -1}).status_code == 422
        assert client.patch("/api/preferences", json={"preferenceStrength": {"skills": "MUST"}}).status_code == 422
        assert client.patch("/api/profile", json={"notAProfileField": True}).status_code == 422
        assert client.patch("/api/preferences", json={}).status_code == 422


def test_storage_failure_returns_safe_503_for_both_apis(tmp_path):
    unusable_path = tmp_path / "directory-not-a-db"
    unusable_path.mkdir()
    with TestClient(create_app(Settings(database_url=_database_url(unusable_path)))) as client:
        profile = client.get("/api/profile")
        preferences = client.put("/api/preferences", json={})
    assert profile.status_code == preferences.status_code == 503
    assert str(tmp_path) not in profile.text + preferences.text


def test_search_still_requires_and_accepts_existing_explicit_request_contract(tmp_path):
    with TestClient(create_app(Settings(database_url=_database_url(tmp_path / "search.db")))) as client:
        assert client.put("/api/profile", json={"skills": ["Python"]}).status_code == 200
        assert client.put("/api/preferences", json={"jobTitles": ["Engineer"]}).status_code == 200
        explicit = client.post("/api/search", json={"profile": {}, "preferences": {}})
        missing_body_fields = client.post("/api/search", json={})
    assert explicit.status_code == 200
    assert missing_body_fields.status_code == 422
