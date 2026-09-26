from collections.abc import AsyncIterator, Callable
from typing import Protocol, TypeVar

T = TypeVar("T")
Cursor = TypeVar("Cursor")


class Paginator(Protocol[T, Cursor]):
    async def pages(self) -> AsyncIterator[list[T]]: ...


class CursorPaginator:
    """Generic cursor iteration; source-specific cursor extraction is injected."""

    def __init__(self, fetch_page: Callable[[str | None], object], next_cursor: Callable[[object], str | None]):
        self._fetch_page = fetch_page
        self._next_cursor = next_cursor

    async def pages(self) -> AsyncIterator[object]:
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            page = await self._fetch_page(cursor)  # type: ignore[misc]
            yield page
            cursor = self._next_cursor(page)
            if cursor is None or cursor in seen:
                return
            seen.add(cursor)
