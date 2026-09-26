from app.services._base import NotImplementedService


class ProfileService(NotImplementedService):
    async def parse_cv(self, cv_text: str) -> None:
        self._not_implemented("ProfileService.parse_cv")
