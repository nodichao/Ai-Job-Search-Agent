from app.services._base import NotImplementedService


class FilteringService(NotImplementedService):
    def filter(self, criteria: object, offers: list[object]) -> None:
        self._not_implemented("FilteringService.filter")
