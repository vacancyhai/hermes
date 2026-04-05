"""Async database session management via SQLAlchemy 2.0."""

from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
    connect_args={"prepared_statement_cache_size": 0},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for Celery tasks (converts asyncpg URL → psycopg2)
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(_sync_url, pool_size=5, pool_pre_ping=True)
