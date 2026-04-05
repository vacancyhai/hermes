"""Application configuration from environment variables."""

from pydantic import model_validator
from pydantic_settings import BaseSettings

_DEFAULT_REDIS_URL = "redis://redis:6379/0"


class Settings(BaseSettings):
    """Settings loaded from .env file and environment variables."""

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_PORT: int = 8000

    # PostgreSQL (through PgBouncer)
    DATABASE_URL: str = "postgresql+asyncpg://hermes_user:@pgbouncer:5432/hermes_db"
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str = _DEFAULT_REDIS_URL
    REDIS_PASSWORD: str = ""
    REDIS_KEY_PREFIX: str = "hermes"

    # Celery
    CELERY_BROKER_URL: str = _DEFAULT_REDIS_URL
    CELERY_RESULT_BACKEND: str = _DEFAULT_REDIS_URL

    # Email
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_DEFAULT_SENDER: str = "noreply@example.com"
    MAIL_ENABLED: bool = False

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES: int = 900  # 15 minutes

    # Firebase (push notifications)
    FIREBASE_CREDENTIALS_PATH: str = ""
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800  # 7 days

    # PDF / AI extraction
    PDF_UPLOAD_DIR: str = "/app/uploads/pdfs"
    PDF_MAX_SIZE_MB: int = 10
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-3-5-sonnet-20241022"
    PDF_KEEP_AFTER_EXTRACTION: bool = (
        False  # Set True to retain PDFs after AI extraction
    )

    # Firebase Auth (frontend JS SDK config)
    FIREBASE_WEB_API_KEY: str = ""
    FIREBASE_AUTH_DOMAIN: str = ""
    FIREBASE_PROJECT_ID: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:8080"

    # SEO
    SITE_URL: str = "http://localhost:8080"
    SITEMAP_PATH: str = "/app/sitemap.xml"

    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: str = ""  # Set to activate Telegram notifications

    # Notification delivery delays (staggered mode, in seconds)
    NOTIFY_EMAIL_DELAY: int = 900  # 15 minutes
    NOTIFY_WHATSAPP_DELAY: int = 3600  # 1 hour
    NOTIFY_TELEGRAM_DELAY: int = 900  # 15 minutes

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:8081"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.APP_ENV == "production":
            if self.JWT_SECRET_KEY.startswith("change-me"):
                raise ValueError(
                    "JWT_SECRET_KEY must not use the default value in production"
                )
        return self


settings = Settings()
