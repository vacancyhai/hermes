"""Hermes Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging
import app.models  # noqa: F401 — register all models for SQLAlchemy relationships
from app.routers import auth, health, jobs, notifications, users, admin, applications


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_logging()
    yield


app = FastAPI(
    title="Hermes API",
    description="Government Job Vacancy Portal — Backend API",
    version="0.1.0",
    docs_url="/api/v1/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/api/v1/redoc" if settings.APP_ENV == "development" else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — all under /api/v1
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(notifications.router)
app.include_router(admin.router)
