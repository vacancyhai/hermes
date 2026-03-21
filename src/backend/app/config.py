"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from .env file and environment variables."""

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_PORT: int = 8000

    # PostgreSQL (through PgBouncer)
    DATABASE_URL: str = "postgresql+asyncpg://hermes_user:hermes_pass@pgbouncer:6432/hermes_db"
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_PASSWORD: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Email
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_DEFAULT_SENDER: str = "noreply@example.com"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES: int = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:8081"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
