from app.services._base import NotImplementedService


class RecommendationService(NotImplementedService):
    def recommend(self, *args: object, **kwargs: object) -> None:
        self._not_implemented("RecommendationService.recommend")
