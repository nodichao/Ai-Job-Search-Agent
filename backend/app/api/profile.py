from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

from app.core.errors import PersistenceError
from app.domain.user_profile import UserProfile
from app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ParseCvRequest(BaseModel):
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


@router.post("/parse-cv", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def parse_cv(_request: ParseCvRequest) -> None:
    raise HTTPException(status_code=501, detail="CV extraction is not implemented yet.")
