from app.connectors.common.http import HttpJsonFetcher
from app.core.config import Settings
from app.services.connector_runtime import build_search_runtime


def test_default_configuration_composes_no_live_sources():
    runtime = build_search_runtime(Settings())
    assert runtime.pipeline is not None
    assert all(not status.active_for_search for status in runtime.connectors)


def test_lever_requires_explicit_enable_flag_and_site():
    missing_site = build_search_runtime(Settings(lever_enabled=True))
    lever_state = next(state for state in missing_site.connectors if state.name == "Lever")
    assert not lever_state.active_for_search
    assert "LEVER_SITE" in lever_state.reason

    configured = build_search_runtime(Settings(lever_enabled=True, lever_site="company-board"))
    lever_state = next(state for state in configured.connectors if state.name == "Lever")
    assert lever_state.active_for_search
    assert lever_state.status == "access pending"


def test_remoteok_requires_explicit_opt_in():
    disabled = build_search_runtime(Settings(remoteok_enabled=False))
    assert not next(state for state in disabled.connectors if state.name == "RemoteOK").active_for_search

    enabled = build_search_runtime(Settings(remoteok_enabled=True), fetcher=HttpJsonFetcher(timeout_seconds=1))
    remoteok_state = next(state for state in enabled.connectors if state.name == "RemoteOK")
    assert remoteok_state.active_for_search
    assert remoteok_state.status == "development"
    assert "storage terms" in remoteok_state.reason


def test_greenhouse_stays_inactive_without_production_normalizer():
    runtime = build_search_runtime(Settings())
    state = next(state for state in runtime.connectors if state.name == "Greenhouse")
    assert state.status == "access pending"
    assert not state.active_for_search
    assert "normalizer" in state.reason


def test_invalid_explicit_remoteok_endpoint_is_reported_unavailable():
    runtime = build_search_runtime(Settings(remoteok_enabled=True, remoteok_endpoint="not-a-url"))
    state = next(state for state in runtime.connectors if state.name == "RemoteOK")
    assert not state.active_for_search
    assert "absolute HTTP(S) URL" in state.reason
