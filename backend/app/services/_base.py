class NotImplementedService:
    """Shared explicit boundary for capabilities not yet implemented."""

    @staticmethod
    def _not_implemented(name: str) -> None:
        raise NotImplementedError(f"{name} is an architectural boundary only in Task 1")
