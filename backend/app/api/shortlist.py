from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.errors import ShortlistDuplicateError, ShortlistIdentityError, ShortlistPersistenceError
from app.domain.job_offer import JobOffer
from app.domain.shortlist import ShortlistEntry, ShortlistStatusUpdate
from app.services.shortlist_service import ShortlistService


router = APIRouter(prefix="/api/shortlist", tags=["shortlist"])


def _service(request: Request) -> ShortlistService:
    return request.app.state.shortlist_service


def _raise_storage_unavailable() -> None:
    raise HTTPException(status_code=503, detail="Shortlist storage is temporarily unavailable")


@router.post("", response_model=ShortlistEntry, status_code=status.HTTP_201_CREATED)
def add_offer(offer: JobOffer, request: Request) -> ShortlistEntry:
    try:
        return _service(request).add(offer)
    except ShortlistIdentityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ShortlistDuplicateError as exc:
        raise HTTPException(status_code=409, detail="Offer is already in the shortlist") from exc
    except ShortlistPersistenceError:
        _raise_storage_unavailable()


@router.get("", response_model=list[ShortlistEntry])
def list_offers(request: Request) -> list[ShortlistEntry]:
    try:
        return _service(request).list()
    except ShortlistPersistenceError:
        _raise_storage_unavailable()


@router.get("/{entry_id}", response_model=ShortlistEntry)
def get_offer(entry_id: str, request: Request) -> ShortlistEntry:
    try:
        entry = _service(request).get(entry_id)
    except ShortlistPersistenceError:
        _raise_storage_unavailable()
    if entry is None:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")
    return entry


@router.patch("/{entry_id}", response_model=ShortlistEntry)
def update_offer(entry_id: str, update: ShortlistStatusUpdate, request: Request) -> ShortlistEntry:
    try:
        entry = _service(request).update_status(entry_id, update.status)
    except ShortlistPersistenceError:
        _raise_storage_unavailable()
    if entry is None:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(entry_id: str, request: Request) -> Response:
    try:
        deleted = _service(request).delete(entry_id)
    except ShortlistPersistenceError:
        _raise_storage_unavailable()
    if not deleted:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
