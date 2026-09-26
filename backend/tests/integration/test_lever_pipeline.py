import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.lever import LeverConnector, LeverNormalizer, LeverSiteContext
from app.domain.search_criteria import SearchCriteria

FIXTURES = Path(__file__).parents[1] / "fixtures" / "lever"


@pytest.mark.asyncio
async def test_lever_fixture_flows_through_connector_raw_and_canonical_boundaries():
    seen = []
    def handler(request):
        seen.append(request)
        name = "page_one.json" if request.url.params["skip"] == "0" else "page_two.json"
        return httpx.Response(200, json=json.loads((FIXTURES / name).read_text(encoding="utf-8")))
    retrieved_at = datetime(2026, 9, 26, tzinfo=timezone.utc)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        raw = await LeverConnector(HttpJsonFetcher(client=client), LeverSiteContext("board", "Example"), page_size=2, clock=lambda: retrieved_at).search(SearchCriteria())
    canonical = [LeverNormalizer().normalize(item) for item in raw]
    assert len(raw) == len(canonical) == 3
    assert canonical[0].identity.source_id == raw[0].source_id
    assert canonical[0].source.retrieved_at == retrieved_at
    assert canonical[0].position.title == "Platform Engineer"
    assert "categories" not in canonical[0].model_dump(mode="json")
    assert "skip" in raw[0].provenance and "categories" in raw[0].payload
