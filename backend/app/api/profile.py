from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ParseCvRequest(BaseModel):
    cv_text: str = Field(min_length=1, max_length=100_000)


@router.post("/parse-cv", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def parse_cv(_request: ParseCvRequest) -> None:
    raise HTTPException(status_code=501, detail="CV extraction is not implemented yet.")
