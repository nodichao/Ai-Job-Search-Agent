from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.search import router as search_router
from app.api.shortlist import router as shortlist_router
from app.api.preferences import router as preferences_router
from app.core.logging import configure_logging
from app.core.config import Settings
from app.connectors.common.http import HttpJsonFetcher
from app.services.connector_runtime import SearchRuntime, build_search_runtime
from app.repositories.shortlist_repository import ShortlistRepository
from app.repositories.sqlite_shortlist_repository import SQLiteShortlistRepository
from app.services.shortlist_service import ShortlistService
from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.sqlite_user_settings_repository import SQLiteUserSettingsRepository
from app.services.user_settings_service import UserSettingsService

configure_logging()


def create_app(
    settings: Settings | None = None,
    *,
    runtime: SearchRuntime | None = None,
    fetcher: HttpJsonFetcher | None = None,
    shortlist_repository: ShortlistRepository | None = None,
    user_settings_repository: UserSettingsRepository | None = None,
) -> FastAPI:
    application = FastAPI(title="AI Job Search Agent API", version="0.1.0")
    app_settings = settings or Settings.from_env()
    application.state.search_runtime = runtime or build_search_runtime(app_settings, fetcher=fetcher)
    repository = shortlist_repository or SQLiteShortlistRepository(app_settings.database_url)
    application.state.shortlist_service = ShortlistService(repository)
    settings_repository = user_settings_repository or SQLiteUserSettingsRepository(app_settings.database_url)
    application.state.user_settings_service = UserSettingsService(settings_repository)
    application.include_router(health_router)
    application.include_router(profile_router)
    application.include_router(search_router)
    application.include_router(shortlist_router)
    application.include_router(preferences_router)
    return application


app = create_app()
