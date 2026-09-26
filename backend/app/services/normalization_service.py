from app.services._base import NotImplementedService


class NormalizationService(NotImplementedService):
    def normalize(self, raw_offers: list[object]) -> None:
        self._not_implemented("NormalizationService.normalize")
