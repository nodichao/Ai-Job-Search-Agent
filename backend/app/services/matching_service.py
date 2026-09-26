from app.services._base import NotImplementedService


class MatchingService(NotImplementedService):
    def match(self, *args: object, **kwargs: object) -> None:
        self._not_implemented("MatchingService.match")
