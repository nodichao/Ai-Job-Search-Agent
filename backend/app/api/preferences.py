from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.errors import PersistenceError
from app.domain.search_preferences import SearchPreferences
from app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _service(request: Request) -> UserSettingsService:
    return request.app.state.user_settings_service


def _storage_error() -> None:
    raise HTTPException(status_code=503, detail="User settings storage is temporarily unavailable")


@router.get("", response_model=SearchPreferences)
def get_preferences(request: Request) -> SearchPreferences:
    try:
        preferences = _service(request).get_preferences()
    except PersistenceError:
        _storage_error()
    if preferences is None:
        raise HTTPException(status_code=404, detail="Search preferences have not been saved")
    return preferences


@router.put("", response_model=SearchPreferences)
def replace_preferences(preferences: SearchPreferences, request: Request) -> SearchPreferences:
    try:
        return _service(request).replace_preferences(preferences)
    except PersistenceError:
        _storage_error()


@router.patch("", response_model=SearchPreferences)
def patch_preferences(request: Request, changes: dict[str, Any] = Body(...)) -> SearchPreferences:
    try:
        return _service(request).patch_preferences(changes)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Search preferences have not been saved") from exc
    except ValidationError as exc:
        raise RequestValidationError([{**item, "loc": ("body", *item["loc"])} for item in exc.errors()]) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError:
        _storage_error()
