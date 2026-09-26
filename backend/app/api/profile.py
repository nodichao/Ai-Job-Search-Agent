from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.errors import LLMError, PersistenceError
from app.domain.user_profile import UserProfile
from app.services.cv_document_extractor import CvDocumentError, MAX_CV_FILE_BYTES
from app.services.profile_service import ProfileService
from app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ParseCvRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cv_text: str = Field(min_length=1, max_length=100_000)


def _service(request: Request) -> UserSettingsService:
    return request.app.state.user_settings_service


def _storage_error() -> None:
    raise HTTPException(status_code=503, detail="User settings storage is temporarily unavailable")


@router.get("", response_model=UserProfile)
def get_profile(request: Request) -> UserProfile:
    try:
        profile = _service(request).get_profile()
    except PersistenceError:
        _storage_error()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile has not been saved")
    return profile


@router.put("", response_model=UserProfile)
def replace_profile(profile: UserProfile, request: Request) -> UserProfile:
    try:
        return _service(request).replace_profile(profile)
    except PersistenceError:
        _storage_error()


@router.patch("", response_model=UserProfile)
def patch_profile(request: Request, changes: dict[str, Any] = Body(...)) -> UserProfile:
    try:
        return _service(request).patch_profile(changes)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Profile has not been saved") from exc
    except ValidationError as exc:
        raise RequestValidationError([{**item, "loc": ("body", *item["loc"])} for item in exc.errors()]) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError:
        _storage_error()


def _profile_service(request: Request) -> ProfileService:
    return request.app.state.profile_service


@router.post("/parse-cv", response_model=UserProfile)
async def parse_cv(request: Request) -> UserProfile:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
    try:
        if content_type == "application/json":
            try:
                payload = await request.json()
                body = ParseCvRequest.model_validate(payload)
            except (ValueError, ValidationError) as exc:
                errors = exc.errors() if isinstance(exc, ValidationError) else [{"type": "json_invalid", "loc": (), "msg": "Invalid JSON", "input": None}]
                raise RequestValidationError([
                    {
                        "type": item.get("type", "value_error"),
                        "loc": ("body", *item.get("loc", ())),
                        "msg": item.get("msg", "Invalid request"),
                    }
                    for item in errors
                ]) from exc
            return await _profile_service(request).parse_cv(body.cv_text)

        if content_type == "multipart/form-data":
            try:
                form = await request.form(max_files=1, max_fields=0, max_part_size=MAX_CV_FILE_BYTES)
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid multipart CV upload") from None
            try:
                if set(form.keys()) != {"file"}:
                    raise HTTPException(status_code=422, detail="Upload one CV file using the 'file' field")
                uploaded = form.get("file")
                if not isinstance(uploaded, StarletteUploadFile):
                    raise HTTPException(status_code=422, detail="A CV file is required")
                if uploaded.size is not None and uploaded.size > MAX_CV_FILE_BYTES:
                    raise HTTPException(status_code=413, detail="Uploaded CV exceeds the 5 MiB limit")
                content = await uploaded.read(MAX_CV_FILE_BYTES + 1)
                if len(content) > MAX_CV_FILE_BYTES:
                    raise HTTPException(status_code=413, detail="Uploaded CV exceeds the 5 MiB limit")
                return await _profile_service(request).parse_cv_file(
                    uploaded.filename or "", uploaded.content_type, content
                )
            finally:
                await form.close()

        raise HTTPException(status_code=415, detail="Use JSON cv_text or a PDF/DOCX multipart upload")
    except CvDocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except LLMError:
        raise HTTPException(status_code=502, detail="Profile extraction service is unavailable") from None
