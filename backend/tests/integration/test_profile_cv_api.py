from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import LLMError
from app.domain.user_profile import UserProfile
from app.main import create_app
from app.services.cv_document_extractor import DOCX_MIME_TYPE, PDF_MIME_TYPE


class FakeLLM:
    def __init__(self, profile=None, error=None):
        self.profile = profile or UserProfile(skills=["Python"], jobTitles=["Backend Engineer"])
        self.error = error
        self.calls = []

    async def extract_profile(self, cv_text):
        self.calls.append(cv_text)
        if self.error:
            raise self.error
        return self.profile


def _settings(tmp_path):
    return Settings(database_url=f"sqlite:///{tmp_path / 'profile.db'}")


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


def test_parse_cv_json_returns_canonical_profile_and_does_not_overwrite_saved_profile(tmp_path):
    llm = FakeLLM()
    with TestClient(create_app(_settings(tmp_path), llm_service=llm)) as client:
        saved = client.put("/api/profile", json={"skills": ["Go"], "jobTitles": ["SRE"]}).json()
        response = client.post("/api/profile/parse-cv", json={"cv_text": "Python backend engineer"})
        after = client.get("/api/profile").json()

    assert response.status_code == 200
    assert response.json() == {
        "skills": ["Python"], "jobTitles": ["Backend Engineer"], "experience": [],
        "totalExperienceYears": None, "education": [], "languages": [], "domains": [], "rawSourceMetadata": {},
    }
    assert after == saved
    assert llm.calls == ["Python backend engineer"]


def test_parse_cv_rejects_invalid_empty_and_unsupported_input_without_llm_call(tmp_path):
    llm = FakeLLM()
    with TestClient(create_app(_settings(tmp_path), llm_service=llm)) as client:
        missing = client.post("/api/profile/parse-cv", json={})
        extra = client.post("/api/profile/parse-cv", json={"cv_text": "Valid", "extra": 1})
        empty = client.post("/api/profile/parse-cv", json={"cv_text": "  "})
        oversize_text = "PRIVATE-CV-MARKER" + "x" * 100_000
        oversize = client.post("/api/profile/parse-cv", json={"cv_text": oversize_text})
        unsupported = client.post("/api/profile/parse-cv", content=b"cv", headers={"content-type": "text/plain"})
        bad_file = client.post("/api/profile/parse-cv", files={"file": ("cv.txt", b"CV", "text/plain")})

    assert [missing.status_code, extra.status_code, empty.status_code, oversize.status_code, unsupported.status_code, bad_file.status_code] == [422, 422, 422, 422, 415, 422]
    assert "PRIVATE-CV-MARKER" not in oversize.text
    assert llm.calls == []


def test_parse_cv_handles_provider_failure_without_leaking_details(tmp_path):
    llm = FakeLLM(error=LLMError("provider error containing personal cv data"))
    with TestClient(create_app(_settings(tmp_path), llm_service=llm)) as client:
        response = client.post("/api/profile/parse-cv", json={"cv_text": "private CV text"})
    assert response.status_code == 502
    assert "personal cv data" not in response.text
    assert "private CV text" not in response.text


def test_parse_cv_accepts_pdf_file_without_persisting_upload(tmp_path):
    llm = FakeLLM()
    pdf = _minimal_pdf("Python candidate")
    with TestClient(create_app(_settings(tmp_path), llm_service=llm)) as client:
        response = client.post(
            "/api/profile/parse-cv",
            files={"file": ("cv.pdf", pdf, PDF_MIME_TYPE)},
        )
    assert response.status_code == 200
    assert llm.calls == ["Python candidate"]


def test_parse_cv_accepts_valid_docx_upload_and_does_not_call_external_provider(tmp_path):
    # Minimal DOCX package with one WordprocessingML text run.
    import io
    from zipfile import ZipFile

    content = io.BytesIO()
    with ZipFile(content, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Python candidate</w:t></w:r></w:p></w:body></w:document>',
        )
    llm = FakeLLM()
    with TestClient(create_app(_settings(tmp_path), llm_service=llm)) as client:
        response = client.post(
            "/api/profile/parse-cv",
            files={"file": ("cv.docx", content.getvalue(), DOCX_MIME_TYPE)},
        )
    assert response.status_code == 200
    assert llm.calls == ["Python candidate"]


def test_application_start_and_health_do_not_create_or_call_llm_client(tmp_path):
    app = create_app(_settings(tmp_path))
    adapter = app.state.profile_service._llm_service
    assert adapter._client is None
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
    assert adapter._client is None
