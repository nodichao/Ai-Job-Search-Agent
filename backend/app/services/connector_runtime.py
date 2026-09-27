"""Central, side-effect-free construction of configured search connectors."""
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from app.connectors.common.http import HttpJsonFetcher
from app.connectors.lever import LeverConnector, LeverSiteContext
from app.connectors.himalayas import HimalayasConnector
from app.connectors.remoteok import RemoteOKConnector
from app.connectors.common.retry import RetryPolicy
from app.core.config import Settings
from app.services.normalization_service import NormalizationService
from app.services.recommendation_service import RecommendationPolicy, RecommendationService
from app.services.ranking_service import RankingService
from app.services.search_pipeline import SearchPipeline
from app.services.search_service import ConnectorBinding, SearchService


class ConnectorAvailability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    status: str
    active_for_search: bool = Field(alias="activeForSearch")
    reason: str


@dataclass(frozen=True)
class SearchRuntime:
    pipeline: SearchPipeline
    connectors: tuple[ConnectorAvailability, ...]


def build_search_runtime(
    settings: Settings,
    *,
    fetcher: HttpJsonFetcher | None = None,
) -> SearchRuntime:
    """Build configured connectors without performing network requests.

    Sources with explicit enablement are constructed without making requests.
    Greenhouse remains inactive because it has no production parser/normalizer.
    """
    http = fetcher or HttpJsonFetcher(
        timeout_seconds=settings.request_timeout_seconds,
        retry_policy=RetryPolicy(),
    )
    bindings: list[ConnectorBinding] = []
    states: list[ConnectorAvailability] = []

    if settings.himalayas_enabled:
        bindings.append(ConnectorBinding(HimalayasConnector(
            http, max_results=settings.max_results_per_source
        )))
        states.append(ConnectorAvailability(
            name="Himalayas",
            status="development",
            activeForSearch=True,
            reason="Enabled; uses the documented public JSON browse feed and cursor. Attribution is required; rate limits apply; generic search criteria are not translated into undocumented filters.",
        ))
    else:
        states.append(ConnectorAvailability(
            name="Himalayas",
            status="development",
            activeForSearch=False,
            reason="Disabled by HIMALAYAS_ENABLED=false.",
        ))

    if settings.remoteok_enabled and settings.remoteok_endpoint:
        try:
            remoteok = RemoteOKConnector(http, settings.remoteok_endpoint)
        except ValueError:
            states.append(ConnectorAvailability(
                name="RemoteOK",
                status="development",
                activeForSearch=False,
                reason="REMOTEOK_ENDPOINT must be an absolute HTTP(S) URL without embedded credentials.",
            ))
        else:
            bindings.append(ConnectorBinding(remoteok))
            states.append(ConnectorAvailability(
                name="RemoteOK",
                status="development",
                activeForSearch=True,
                reason="Explicitly enabled; current feed shape is verified, but request limits, storage terms, and UI attribution remain unresolved.",
            ))
    else:
        reason = (
            "REMOTEOK_ENDPOINT is missing."
            if settings.remoteok_enabled
            else "Disabled by default; set REMOTEOK_ENABLED=true to opt in."
        )
        states.append(ConnectorAvailability(
            name="RemoteOK", status="development", activeForSearch=False, reason=reason
        ))

    if settings.lever_enabled and settings.lever_site and settings.lever_site.strip():
        try:
            context = LeverSiteContext(settings.lever_site)
        except ValueError:
            states.append(ConnectorAvailability(
                name="Lever",
                status="access pending",
                activeForSearch=False,
                reason="LEVER_SITE is invalid; no request will be made.",
            ))
        else:
            bindings.append(ConnectorBinding(
                LeverConnector(
                    http,
                    context,
                    max_results=settings.max_results_per_source,
                )
            ))
            states.append(ConnectorAvailability(
                name="Lever",
                status="access pending",
                activeForSearch=True,
                reason="Explicitly enabled for a configured SITE; third-party usage conditions remain pending.",
            ))
    else:
        if not settings.lever_enabled:
            reason = "Disabled by default; access and third-party usage conditions remain pending."
        else:
            reason = "LEVER_SITE is required; no request will be made without an explicit site."
        states.append(ConnectorAvailability(
            name="Lever", status="access pending", activeForSearch=False, reason=reason
        ))

    states.append(ConnectorAvailability(
        name="Greenhouse",
        status="access pending",
        activeForSearch=False,
        reason="No production parser/normalizer or employer authorization is configured.",
    ))

    search_service = SearchService(bindings)
    pipeline = SearchPipeline(
        search_service,
        NormalizationService(),
        recommendation_service=RecommendationService(RecommendationPolicy(
            score_threshold=settings.recommendation_score_threshold,
            minimum_confidence=settings.recommendation_minimum_confidence,
        )),
        ranking_service=RankingService(),
    )
    return SearchRuntime(pipeline=pipeline, connectors=tuple(states))
