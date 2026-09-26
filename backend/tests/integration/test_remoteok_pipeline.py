import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.remoteok import RemoteOKConnector, RemoteOKNormalizer
from app.domain.search_criteria import SearchCriteria

FIXTURE = Path(__file__).parents[1] / "fixtures" / "remoteok" / "offer_list.json"
ENDPOINT = "https://remoteok.example.invalid/jobs.json"


@pytest.mark.asyncio
async def test_remoteok_fixture_crosses_connector_raw_and_canonical_boundaries() -> None:
    source_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    retrieved_at = datetime(2026, 9, 26, tzinfo=timezone.utc)
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=source_payload))

    async with httpx.AsyncClient(transport=transport) as client:
        connector = RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT, clock=lambda: retrieved_at)
        raw_offers = await connector.search(SearchCriteria(skills=["python"], remote=True))
    normalized = [RemoteOKNormalizer().normalize(raw) for raw in raw_offers]

    assert len(raw_offers) == len(normalized) == 1
    assert raw_offers[0].payload == source_payload[0]
    assert normalized[0].position.title == "Senior Platform Engineer"
    assert normalized[0].identity.source_id == raw_offers[0].source_id
    assert normalized[0].source.name == "RemoteOK"
    assert normalized[0].position.summary is None
    assert "unmapped_source_field" not in normalized[0].model_dump(mode="json")
