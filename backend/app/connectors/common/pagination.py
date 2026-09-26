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


class PagePaginator:
    """Bounded offset pagination for APIs that expose skip/limit parameters."""

    def __init__(self, fetch_page: Callable[[int, int], object], *, page_size: int, max_results: int):
        if page_size < 1 or max_results < 1:
            raise ValueError("page_size and max_results must be positive")
        self._fetch_page = fetch_page
        self._page_size = page_size
        self._max_results = max_results

    async def pages(self) -> AsyncIterator[list[object]]:
        skip = 0
        yielded = 0
        while yielded < self._max_results:
            requested = min(self._page_size, self._max_results - yielded)
            response = await self._fetch_page(skip, requested)  # type: ignore[misc]
            if not isinstance(response, list):
                raise TypeError("Page fetcher must return a list")
            if not response:
                return
            page = response[:requested]
            yield page
            yielded += len(page)
            if len(response) < requested:
                return
            skip += requested
