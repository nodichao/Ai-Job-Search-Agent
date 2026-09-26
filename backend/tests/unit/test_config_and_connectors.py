import pytest
import httpx

from app.core.config import Settings
from app.core.errors import ConfigurationError, RateLimitError, SourceUnavailableError
from app.connectors.common.retry import RetryPolicy
from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.pagination import CursorPaginator
from app.connectors.base import RawOffer


def test_settings_load_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "4")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.test")
    settings = Settings.from_env()
    assert settings.request_timeout_seconds == 4
    assert settings.cors_origins == ("http://localhost:3000", "https://example.test")


def test_connectors_default_to_disabled_and_load_explicit_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REMOTEOK_ENABLED", raising=False)
    monkeypatch.delenv("LEVER_ENABLED", raising=False)
    monkeypatch.setenv("LEVER_SITE", "example-site")
    settings = Settings.from_env()
    assert settings.remoteok_enabled is False
    assert settings.lever_enabled is False
    assert settings.remoteok_endpoint == "https://remoteok.com/api"
    assert settings.lever_site == "example-site"


def test_recommendation_policy_is_configurable_and_range_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RECOMMENDATION_SCORE_THRESHOLD", "72")
    monkeypatch.setenv("RECOMMENDATION_MINIMUM_CONFIDENCE", "0.65")
    settings = Settings.from_env()
    assert settings.recommendation_score_threshold == 72
    assert settings.recommendation_minimum_confidence == 0.65

    monkeypatch.setenv("RECOMMENDATION_MINIMUM_CONFIDENCE", "1.2")
    with pytest.raises(ConfigurationError):
        Settings.from_env()


def test_invalid_settings_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REMOTEOK_ENABLED", "sometimes")
    with pytest.raises(ConfigurationError):
        Settings.from_env()


def test_retry_policy_defaults_and_validation() -> None:
    assert RetryPolicy().max_attempts == 3
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_http_fetcher_uses_configured_default_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "7")
    assert HttpJsonFetcher()._timeout == 7


def test_raw_offer_preserves_source_payload_and_provenance() -> None:
    offer = RawOffer(source_name="Example", source_id="1", payload={"title": "Engineer"}, provenance={"feed": "declared"})
    assert offer.payload["title"] == "Engineer"
    assert offer.provenance["feed"] == "declared"


@pytest.mark.asyncio
async def test_http_json_fetcher_returns_json_without_live_network() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"items": []}))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await HttpJsonFetcher(client=client).get("https://source.invalid/jobs")
    assert result == {"items": []}


@pytest.mark.asyncio
async def test_http_json_fetcher_does_not_retry_rate_limits() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RateLimitError):
            await HttpJsonFetcher(client=client).get("https://source.invalid/jobs")
    assert calls == 1


@pytest.mark.asyncio
async def test_http_json_fetcher_retries_transient_network_errors_with_a_bound() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpJsonFetcher(client=client, retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0))
        assert await fetcher.get("https://source.invalid/jobs") == {"ok": True}
    assert calls == 2


@pytest.mark.asyncio
async def test_http_json_fetcher_maps_exhausted_network_errors() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("connection refused", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpJsonFetcher(client=client, retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0))
        with pytest.raises(SourceUnavailableError):
            await fetcher.get("https://source.invalid/jobs")
    assert calls == 2


@pytest.mark.asyncio
async def test_cursor_paginator_stops_when_cursor_repeats() -> None:
    async def fetch(cursor: str | None) -> dict[str, object]:
        return {"cursor": "same", "request_cursor": cursor}

    paginator = CursorPaginator(fetch, lambda page: page["cursor"])
    pages = [page async for page in paginator.pages()]
    assert len(pages) == 2
