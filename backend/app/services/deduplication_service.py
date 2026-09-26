from app.services._base import NotImplementedService


class DeduplicationService(NotImplementedService):
    def deduplicate(self, offers: list[object]) -> None:
        self._not_implemented("DeduplicationService.deduplicate")
