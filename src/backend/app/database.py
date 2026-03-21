"""Async database session management via SQLAlchemy 2.0."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
