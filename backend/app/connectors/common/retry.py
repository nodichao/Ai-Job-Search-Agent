from dataclasses import dataclass
import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.25
    maximum_delay_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.initial_delay_seconds < 0 or self.maximum_delay_seconds < 0:
            raise ValueError("Retry policy values must be non-negative and attempts must be at least one")

    async def run(self, operation: Callable[[], Awaitable[T]], retryable: Callable[[Exception], bool]) -> T:
        delay = self.initial_delay_seconds
        for attempt in range(self.max_attempts):
            try:
                return await operation()
            except Exception as exc:
                if attempt + 1 >= self.max_attempts or not retryable(exc):
                    raise
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.maximum_delay_seconds)
        raise RuntimeError("Unreachable retry state")
