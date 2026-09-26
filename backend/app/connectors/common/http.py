from typing import Any, Protocol
import httpx

from app.core.config import Settings
from app.core.errors import AuthenticationError, ConnectorError, RateLimitError, SourceUnavailableError
from app.connectors.common.retry import RetryPolicy


class AuthStrategy(Protocol):
    """Marker type for explicit, source-approved request authentication."""

    def apply(self, headers: dict[str, str]) -> dict[str, str]: ...


class HttpJsonFetcher:
    def __init__(self, timeout_seconds: float | None = None, client: httpx.AsyncClient | None = None, retry_policy: RetryPolicy | None = None):
        if timeout_seconds is None:
            timeout_seconds = Settings.from_env().request_timeout_seconds
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout = timeout_seconds
        self._client = client
        self._retry = retry_policy or RetryPolicy()

    async def get(self, url: str, *, params: dict[str, object] | None = None, headers: dict[str, str] | None = None) -> Any:
        async def request() -> Any:
            if self._client is not None:
                response = await self._client.get(url, params=params, headers=headers, timeout=self._timeout)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError("The source denied access")
            if response.status_code == 429:
                raise RateLimitError("The source rate limit was reached")
            if response.status_code >= 500:
                raise SourceUnavailableError(f"Source returned HTTP {response.status_code}")
            try:
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise ConnectorError("The source returned an unsuccessful or invalid JSON response") from exc

        def retryable(error: Exception) -> bool:
            return isinstance(error, (httpx.TimeoutException, httpx.NetworkError, SourceUnavailableError))

        try:
            return await self._retry.run(request, retryable)
        except (AuthenticationError, RateLimitError, ConnectorError):
            raise
        except httpx.TimeoutException as exc:
            raise SourceUnavailableError("The source request timed out") from exc
        except httpx.NetworkError as exc:
            raise SourceUnavailableError("The source network request failed") from exc
