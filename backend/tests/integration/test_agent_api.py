import json

from fastapi.testclient import TestClient

from app.connectors.base import RawOffer
from app.core.config import Settings
from app.core.errors import LLMError
from app.domain.user_profile import UserProfile
from app.llm.schemas import MatchExplanationBatch, OfferExplanation
from app.main import create_app
from app.services.connector_runtime import ConnectorAvailability, SearchRuntime
from app.services.normalization_service import NormalizationService
from app.services.search_pipeline import SearchPipeline
from app.services.search_service import ConnectorBinding, SearchService


def _minimal_pdf(text):
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode())
    return bytes(pdf)


class FixtureConnector:
    source_name = "RemoteOK"

    def __init__(self, payload):
        self.offer = RawOffer(source_name=self.source_name, source_id=str(payload["id"]), payload=payload,
                               provenance={"source_url": "https://remoteok.com/"})

    async def search(self, criteria):
        return [self.offer]


class FakeLLM:
    def __init__(self, profile=None, extract_error=None, explain_batch=None, explain_error=None):
        self.profile = profile or UserProfile(skills=["Python"], jobTitles=["Full-Stack Developer"], totalExperienceYears=3)
        self.extract_error = extract_error
        self.explain_batch = explain_batch if explain_batch is not None else MatchExplanationBatch(explanations=[])
        self.explain_error = explain_error
        self.extract_calls = []
        self.explain_calls = []

    async def extract_profile(self, cv_text):
        self.extract_calls.append(cv_text)
        if self.extract_error:
            raise self.extract_error
        return self.profile

    async def explain_match(self, items):
        self.explain_calls.append(items)
        if self.explain_error:
            raise self.explain_error
        return self.explain_batch


def _app(llm, tmp_path, payload=None):
    payload = payload or {
        "id": 900001, "position": "Full-Stack Developer", "company": "SampleCo",
        "tags": ["React", "Node.js"], "location": "Dakar, Senegal",
    }
    runtime = SearchRuntime(
        pipeline=SearchPipeline(SearchService([ConnectorBinding(FixtureConnector(payload))]), NormalizationService()),
        connectors=(ConnectorAvailability(name="RemoteOK", status="development", activeForSearch=True,
                                           reason="deterministic fixture connector"),),
    )
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'agent.db'}")
    return create_app(settings, runtime=runtime, llm_service=llm)


def _preferences():
    return {
        "jobTitles": ["Full-Stack Developer"], "locations": ["Dakar"], "countries": ["Senegal"], "remote": True,
    }


def test_agent_search_runs_the_full_workflow_and_preserves_pipeline_results(tmp_path):
    llm = FakeLLM(explain_batch=MatchExplanationBatch(explanations=[
        OfferExplanation(offerId="900001", summary="Strong overlap.", recommendationContext="Meets threshold"),
    ]))
    with TestClient(_app(llm, tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": json.dumps(_preferences())},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["profile"]["skills"] == ["Python"]
    assert llm.extract_calls and "Full-Stack Developer" in llm.extract_calls[0]

    assert len(body["results"]) == 1
    assert body["results"][0]["position"]["title"] == "Full-Stack Developer"
    assert len(body["matches"]) == 1
    scored = body["matches"][0]
    assert scored["matching"]["score"] is not None
    assert scored["recommendation"]["decision"] in {"RECOMMENDED", "NOT_RECOMMENDED", "INSUFFICIENT_EVIDENCE"}

    # Non-regression: the ranking exposed by the agent endpoint must exactly
    # match what /api/search would compute for the same offer set.
    with TestClient(_app(FakeLLM(), tmp_path, payload=None)) as direct_client:
        direct = direct_client.post("/api/search", json={
            "profile": body["profile"], "preferences": _preferences(),
        })
    assert direct.json()["matches"][0]["matching"]["score"] == scored["matching"]["score"]
    assert direct.json()["matches"][0]["recommendation"]["decision"] == scored["recommendation"]["decision"]
    assert body["ranking"] == direct.json()["ranking"]

    assert len(body["explanations"]) == 1
    assert body["explanations"][0]["source"] == "llm"
    assert body["explanations"][0]["explanation"]["summary"] == "Strong overlap."
    assert body["warnings"] == []
    assert [step["tool"] for step in body["steps"]] == ["parse_cv", "search_jobs", "explain_match"]
    assert all(step["status"] == "success" for step in body["steps"])


def test_agent_search_falls_back_to_deterministic_explanation_when_llm_explain_fails(tmp_path):
    llm = FakeLLM(explain_error=RuntimeError("provider down"))
    with TestClient(_app(llm, tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": json.dumps(_preferences())},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["explanations"][0]["source"] == "fallback"
    assert any("deterministic summary" in warning for warning in body["warnings"])


def test_agent_search_rejects_when_cv_extraction_fails(tmp_path):
    llm = FakeLLM(extract_error=LLMError("provider unavailable"))
    with TestClient(_app(llm, tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": json.dumps(_preferences())},
        )

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()


def test_agent_search_rejects_invalid_file(tmp_path):
    with TestClient(_app(FakeLLM(), tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.txt", b"not a real cv", "text/plain")},
            data={"preferences": json.dumps(_preferences())},
        )

    assert response.status_code == 422


def test_agent_search_rejects_invalid_preferences_json(tmp_path):
    with TestClient(_app(FakeLLM(), tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": "not json"},
        )

    assert response.status_code == 422


def test_agent_search_rejects_unknown_preference_fields(tmp_path):
    with TestClient(_app(FakeLLM(), tmp_path)) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": json.dumps({"unknownField": True})},
        )

    assert response.status_code == 422


def test_agent_search_returns_explicit_empty_result_without_fabricating_offers(tmp_path):
    llm = FakeLLM()
    empty_runtime = SearchRuntime(
        pipeline=SearchPipeline(SearchService([]), NormalizationService()),
        connectors=(),
    )
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'agent-empty.db'}")
    app = create_app(settings, runtime=empty_runtime, llm_service=llm)
    with TestClient(app) as client:
        response = client.post(
            "/api/agent/search",
            files={"file": ("cv.pdf", _minimal_pdf("Full-Stack Developer"), "application/pdf")},
            data={"preferences": json.dumps(_preferences())},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["matches"] == []
    assert body["explanations"] == []
    assert body["ranking"] == {"offers": [], "total": 0}


def test_existing_routes_still_work_alongside_the_agent_endpoint(tmp_path):
    with TestClient(_app(FakeLLM(), tmp_path)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/profile").status_code == 404
        search_response = client.post("/api/search", json={"profile": {}, "preferences": _preferences()})
        assert search_response.status_code == 200
