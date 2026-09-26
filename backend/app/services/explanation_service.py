from app.services._base import NotImplementedService


class ExplanationService(NotImplementedService):
    async def explain(self, *args: object, **kwargs: object) -> None:
        self._not_implemented("ExplanationService.explain")
