from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.search import router as search_router
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(title="AI Job Search Agent API", version="0.1.0")
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(search_router)
