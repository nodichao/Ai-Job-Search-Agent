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


@pytest.mark.asyncio
async def test_remoteok_feed_metadata_does_not_contaminate_canonical_job_offer() -> None:
    source_offer = json.loads(FIXTURE.read_text(encoding="utf-8"))[0]
    feed_metadata = {
        "last_updated": 1790438426,
        "legal": "Credit Remote OK as source and link the original job URL.",
    }
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json=[feed_metadata, source_offer])
    )

    async with httpx.AsyncClient(transport=transport) as client:
        raw_offers = await RemoteOKConnector(HttpJsonFetcher(client=client), ENDPOINT).search(SearchCriteria())
    normalized = RemoteOKNormalizer().normalize(raw_offers[0])
    canonical_json = normalized.model_dump(mode="json", by_alias=True)

    assert len(raw_offers) == 1
    assert raw_offers[0].payload == source_offer
    assert raw_offers[0].provenance["attribution_notice"] == feed_metadata["legal"]
    assert canonical_json["source"]["name"] == "RemoteOK"
    assert str(normalized.identity.offer_url) == "https://remoteok.example.invalid/remote-jobs/735421"
    assert "attribution_notice" not in str(canonical_json)
    assert "last_updated" not in str(canonical_json)
