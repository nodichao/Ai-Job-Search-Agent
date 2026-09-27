from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from app.api.agent import router as agent_router
from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.search import router as search_router
from app.api.shortlist import router as shortlist_router
from app.api.preferences import router as preferences_router
from app.core.logging import configure_logging
from app.core.config import Settings
from app.llm.base import LLMService
from app.llm.groq_service import GroqLLMService
from app.connectors.common.http import HttpJsonFetcher
from app.services.agent_service import AgentService
from app.services.connector_runtime import SearchRuntime, build_search_runtime
from app.repositories.shortlist_repository import ShortlistRepository
from app.repositories.sqlite_shortlist_repository import SQLiteShortlistRepository
from app.services.shortlist_service import ShortlistService
from app.repositories.user_settings_repository import UserSettingsRepository
from app.repositories.sqlite_user_settings_repository import SQLiteUserSettingsRepository
from app.services.user_settings_service import UserSettingsService
from app.services.profile_service import ProfileService

configure_logging()


def create_app(
    settings: Settings | None = None,
    *,
    runtime: SearchRuntime | None = None,
    fetcher: HttpJsonFetcher | None = None,
    shortlist_repository: ShortlistRepository | None = None,
    user_settings_repository: UserSettingsRepository | None = None,
    llm_service: LLMService | None = None,
    agent_service: AgentService | None = None,
) -> FastAPI:
    application = FastAPI(title="AI Job Search Agent API", version="0.1.0")

    @application.exception_handler(RequestValidationError)
    async def redact_search_text_validation_input(request: Request, exc: RequestValidationError):
        if request.url.path == "/api/search/from-text":
            safe_errors = [
                {"type": error.get("type", "value_error"), "loc": error.get("loc", ()),
                 "msg": error.get("msg", "Invalid request")}
                for error in exc.errors()
            ]
            exc = RequestValidationError(safe_errors)
        return await request_validation_exception_handler(request, exc)

    app_settings = settings or Settings.from_env()
    application.state.search_runtime = runtime or build_search_runtime(app_settings, fetcher=fetcher)
    repository = shortlist_repository or SQLiteShortlistRepository(app_settings.database_url)
    application.state.shortlist_service = ShortlistService(repository)
    settings_repository = user_settings_repository or SQLiteUserSettingsRepository(app_settings.database_url)
    application.state.user_settings_service = UserSettingsService(settings_repository)
    configured_llm = llm_service if llm_service is not None else GroqLLMService(
        api_key=app_settings.groq_api_key,
        model=app_settings.groq_model,
        timeout_seconds=app_settings.request_timeout_seconds,
    )
    application.state.llm_service = configured_llm
    application.state.profile_service = ProfileService(configured_llm)
    application.state.agent_service = agent_service or AgentService(
        application.state.profile_service,
        application.state.search_runtime.pipeline,
        configured_llm,
        max_explanations=app_settings.agent_max_explanations,
    )
    application.include_router(health_router)
    application.include_router(profile_router)
    application.include_router(search_router)
    application.include_router(shortlist_router)
    application.include_router(preferences_router)
    application.include_router(agent_router)
    return application


app = create_app()
