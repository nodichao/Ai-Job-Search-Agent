import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.greenhouse import GreenhouseBoardContext, GreenhouseBoardOffer, GreenhouseConnector
from app.core.errors import ConnectorError
from app.domain.search_criteria import SearchCriteria

FIXTURE = Path(__file__).parents[1] / "fixtures" / "greenhouse" / "opaque_board_response.json"
NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)


class ExplicitFixtureParser:
    def parse(self, response, context):
        assert context.board_token == "configured-board"
        # Test-only projection to exercise the parser boundary; it is not an API schema.
        return [GreenhouseBoardOffer(source_id="fixture-1", payload={"opaque": response})]


@pytest.mark.asyncio
async def test_greenhouse_uses_explicit_endpoint_parser_and_board_context():
    body = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=body)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = GreenhouseConnector(HttpJsonFetcher(client=client), GreenhouseBoardContext("configured-board", "Example", "42"),
            endpoint="https://greenhouse.example.invalid/explicit-board", parser=ExplicitFixtureParser(), clock=lambda: NOW)
        offers = await connector.search(SearchCriteria(keywords=["ignored; no undocumented query parameter"]))
    assert seen[0].url.path == "/explicit-board" and seen[0].url.query == b""
    assert offers[0].source_name == "Greenhouse"
    assert offers[0].source_id == "fixture-1"
    assert offers[0].payload == {"opaque": body}
    assert offers[0].retrieved_at == NOW
    assert offers[0].provenance["board_token"] == "configured-board"
    assert offers[0].provenance["company_id"] == "42"


def test_greenhouse_requires_explicit_board_and_endpoint():
    with pytest.raises(ValueError):
        GreenhouseBoardContext("  ")
    with pytest.raises(ValueError):
        GreenhouseConnector(HttpJsonFetcher(), GreenhouseBoardContext("board"), endpoint="/board", parser=ExplicitFixtureParser())


@pytest.mark.asyncio
async def test_greenhouse_rejects_invalid_custom_parser_result():
    class BadParser:
        def parse(self, response, context):
            return [object()]
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))) as client:
        connector = GreenhouseConnector(HttpJsonFetcher(client=client), GreenhouseBoardContext("board"),
            endpoint="https://greenhouse.example.invalid/board", parser=BadParser())
        with pytest.raises(ConnectorError):
            await connector.search(SearchCriteria())
