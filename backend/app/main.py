import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.middleware.error_handlers import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing heavy needed - the async engine connects lazily and
    # migrations are run as a separate step (see docker-compose entrypoint).
    yield
    # Shutdown: dispose the DB engine pool cleanly.
    from app.db.database import engine

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="A visual second-brain / personal knowledge management system.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Register, login, refresh, and session management."},
        {"name": "Nodes", "description": "Knowledge nodes and the graph view."},
        {"name": "Relationships", "description": "Edges connecting knowledge nodes."},
        {"name": "Tags", "description": "User-defined tags."},
        {"name": "Resources", "description": "External references attached to nodes."},
        {"name": "Search", "description": "Full-text search across the knowledge base."},
        {"name": "Analytics", "description": "Knowledge graph statistics and trends."},
        {"name": "Dashboard", "description": "Aggregate personal dashboard data."},
        {"name": "Suggestions", "description": "Rule-based connection and knowledge-gap suggestions."},
        {"name": "Activity", "description": "Permanent activity history."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
