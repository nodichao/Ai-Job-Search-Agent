import pytest

from app.connectors.base import RawOffer
from app.core.config import Settings
from app.core.errors import SourceUnavailableError
from app.domain.search_criteria import SearchCriteria
from app.services.search_service import ConnectorBinding, SearchService


class FakeConnector:
    def __init__(self, source_name: str, *, fail: bool = False, empty: bool = False) -> None:
        self.source_name = source_name
        self.fail = fail
        self.empty = empty
        self.calls = 0

    async def search(self, criteria: SearchCriteria) -> list[RawOffer]:
        self.calls += 1
        if self.fail:
            raise SourceUnavailableError("offline")
        if self.empty:
            return []
        return [RawOffer(source_name=self.source_name, payload={"criteria_keywords": criteria.keywords})]


@pytest.mark.asyncio
async def test_search_service_selects_enabled_connectors_and_aggregates_raw_offers() -> None:
    enabled = FakeConnector("RemoteOK")
    disabled = FakeConnector("Himalayas")
    service = SearchService([
        ConnectorBinding(enabled, enabled=True),
        ConnectorBinding(disabled, enabled=False),
    ])

    offers = await service.search(SearchCriteria(keywords=["engineer"]))

    assert enabled.calls == 1
    assert disabled.calls == 0
    assert len(offers) == 1
    assert offers[0].payload["criteria_keywords"] == ["engineer"]


@pytest.mark.asyncio
async def test_search_service_isolates_a_source_error() -> None:
    failing = FakeConnector("Unavailable", fail=True)
    healthy = FakeConnector("Healthy")
    service = SearchService([ConnectorBinding(failing), ConnectorBinding(healthy)])

    offers = await service.search(SearchCriteria())

    assert failing.calls == 1
    assert healthy.calls == 1
    assert [offer.source_name for offer in offers] == ["Healthy"]


@pytest.mark.asyncio
async def test_remoteok_enable_setting_controls_generic_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REMOTEOK_ENABLED", "false")
    remoteok = FakeConnector("RemoteOK")
    binding = ConnectorBinding(remoteok, enabled=Settings.from_env().remoteok_enabled)

    await SearchService([binding]).search(SearchCriteria())

    assert remoteok.calls == 0


@pytest.mark.asyncio
async def test_search_service_aggregates_three_sources_without_normalizing_them() -> None:
    sources = [FakeConnector(name) for name in ("RemoteOK", "Lever", "Greenhouse")]
    offers = await SearchService([ConnectorBinding(source) for source in sources]).search(SearchCriteria())
    assert [source.calls for source in sources] == [1, 1, 1]
    assert [offer.source_name for offer in offers] == ["RemoteOK", "Lever", "Greenhouse"]
    assert all("criteria_keywords" in offer.payload for offer in offers)


@pytest.mark.asyncio
async def test_search_service_returns_empty_for_no_enabled_or_empty_connectors() -> None:
    disabled = FakeConnector("Disabled")
    empty = FakeConnector("Empty", empty=True)
    assert await SearchService([ConnectorBinding(disabled, enabled=False)]).search(SearchCriteria()) == []
    assert disabled.calls == 0
    assert await SearchService([ConnectorBinding(empty)]).search(SearchCriteria()) == []
    assert empty.calls == 1


@pytest.mark.asyncio
async def test_search_service_returns_empty_when_all_sources_fail_without_logging_payloads(caplog) -> None:
    first = FakeConnector("First", fail=True)
    second = FakeConnector("Second", fail=True)
    results = await SearchService([ConnectorBinding(first), ConnectorBinding(second)]).search(
        SearchCriteria(keywords=["private candidate term"])
    )
    assert results == []
    assert first.calls == second.calls == 1
    assert "private candidate term" not in caplog.text
    assert "offline" not in caplog.text
