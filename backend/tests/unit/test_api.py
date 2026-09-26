from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_live() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unimplemented_routes_are_explicit() -> None:
    response = client.post("/api/search", json={"profile": {}, "preferences": {}})
    assert response.status_code == 501


def test_application_starts_and_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert {"/health", "/api/profile/parse-cv", "/api/search", "/api/search/from-text"} <= paths
