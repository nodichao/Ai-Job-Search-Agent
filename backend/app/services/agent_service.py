from app.services._base import NotImplementedService


class AgentService(NotImplementedService):
    async def run(self, *args: object, **kwargs: object) -> None:
        self._not_implemented("AgentService.run")
