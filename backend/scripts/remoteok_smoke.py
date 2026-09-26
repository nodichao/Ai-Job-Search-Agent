"""Explicit one-request, in-memory RemoteOK connector smoke check."""
import argparse
import asyncio
import sys

import httpx

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.common.retry import RetryPolicy
from app.connectors.remoteok import RemoteOKConnector, RemoteOKNormalizer
from app.core.config import Settings
from app.domain.search_criteria import SearchCriteria


async def _run() -> int:
    settings = Settings.from_env()
    try:
        async with httpx.AsyncClient() as client:
            fetcher = HttpJsonFetcher(
                timeout_seconds=settings.request_timeout_seconds,
                client=client,
                retry_policy=RetryPolicy(max_attempts=1),
            )
            raw_offers = await RemoteOKConnector(fetcher, settings.remoteok_endpoint).search(SearchCriteria())
            normalized = [RemoteOKNormalizer().normalize(raw) for raw in raw_offers]
    except Exception as exc:
        # Do not print URLs, payloads, job text, or exception details.
        print(f"RemoteOK smoke failed ({type(exc).__name__}); response details withheld.", file=sys.stderr)
        return 1

    has_feed_notice = bool(raw_offers) and all(
        isinstance(raw.provenance.get("attribution_notice"), str)
        and bool(raw.provenance.get("attribution_notice"))
        for raw in raw_offers
    )
    print(
        f"HTTP connector path succeeded; received={len(raw_offers)}; "
        f"normalized={len(normalized)}; attribution_metadata={has_feed_notice}; lifecycle=development"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-one-off-read",
        action="store_true",
        help="explicitly authorize one read of the configured RemoteOK public JSON feed",
    )
    arguments = parser.parse_args()
    if not arguments.confirm_one_off_read:
        parser.error("pass --confirm-one-off-read to make one live GET request")
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
