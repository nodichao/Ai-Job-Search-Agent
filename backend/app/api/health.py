from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness endpoint; it does not claim that optional integrations are ready."""
    return {"status": "ok"}
