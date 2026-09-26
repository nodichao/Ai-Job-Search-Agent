from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_live() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_route_returns_empty_results_and_explicit_connector_states_by_default() -> None:
    response = client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["meta"]["total"] == 0
    assert body["meta"]["sources"] == []
    statuses = {item["name"]: item for item in body["meta"]["connectors"]}
    assert set(statuses) == {"RemoteOK", "Lever", "Greenhouse"}
    assert all(not item["activeForSearch"] for item in statuses.values())


def test_search_from_text_validates_required_input_before_parsing() -> None:
    response = client.post("/api/search/from-text", json={"profile": {}})
    assert response.status_code == 422


def test_search_rejects_invalid_request_data() -> None:
    response = client.post("/api/search", json={"profile": {}, "preferences": {"notAField": "x"}})
    assert response.status_code == 422


def test_application_starts_and_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert {"/health", "/api/profile/parse-cv", "/api/search", "/api/search/from-text"} <= paths
