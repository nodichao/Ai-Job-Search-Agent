"""Orchestrate CV text/document extraction and structured profile validation."""
from app.core.errors import LLMError
from app.domain.user_profile import UserProfile
from app.llm.base import LLMService
from app.services.cv_document_extractor import CvDocumentExtractor


class ProfileService:
    def __init__(self, llm_service: LLMService, document_extractor: CvDocumentExtractor | None = None):
        self._llm_service = llm_service
        self._document_extractor = document_extractor or CvDocumentExtractor()

    async def parse_cv(self, cv_text: str) -> UserProfile:
        if not isinstance(cv_text, str) or not cv_text.strip():
            raise ValueError("CV text must not be empty")
        if len(cv_text) > 100_000:
            raise ValueError("CV text exceeds the 100,000 character limit")
        try:
            extracted = await self._llm_service.extract_profile(cv_text)
            profile = UserProfile.model_validate(extracted)
        except Exception:
            # Never include provider errors or CV text in raised API errors.
            raise LLMError("Profile extraction failed") from None
        return profile.model_copy(update={"raw_source_metadata": {}})

    async def parse_cv_file(self, filename: str, media_type: str | None, content: bytes) -> UserProfile:
        text = self._document_extractor.extract_text(filename, media_type, content)
        return await self.parse_cv(text)
