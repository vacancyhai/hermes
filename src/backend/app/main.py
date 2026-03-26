"""Hermes Backend — FastAPI Application."""

import uuid as _uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.logging_config import setup_logging
from app.rate_limit import limiter
import app.models  # noqa: F401 — register all models for SQLAlchemy relationships
from app.routers import auth, health, jobs, notifications, users, admin, applications
from app.routers.job_documents import public_router as job_docs_public_router, admin_router as job_docs_admin_router
from app.routers.entrance_exams import public_router as exams_public_router, admin_router as exams_admin_router
from app.routers.content import admit_cards_router, answer_keys_router, results_router


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

# Attach limiter to app state for SlowAPI
app.state.limiter = limiter


# ─── X-Request-ID Middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Propagate or generate X-Request-ID for every request."""
    request_id = request.headers.get("x-request-id") or _uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ─── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Structured Error Handlers ──────────────────────────────────────────────

def _error_response(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    """Build a structured error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


# Map common detail strings to structured error codes
_ERROR_CODE_MAP = {
    "Email already registered": "VALIDATION_EMAIL_EXISTS",
    "Invalid email format": "VALIDATION_EMAIL_INVALID",
    "Invalid token": "AUTH_INVALID_CREDENTIALS",
    "Invalid token type": "AUTH_INVALID_CREDENTIALS",
    "Token revoked": "AUTH_TOKEN_REVOKED",
    "Token expired": "AUTH_TOKEN_EXPIRED",
    "Invalid token scope": "FORBIDDEN_PERMISSION_DENIED",
    "Admin access required": "FORBIDDEN_ADMIN_ONLY",
    "Operator access required": "FORBIDDEN_PERMISSION_DENIED",
    "User not found or inactive": "NOT_FOUND_USER",
    "Admin not found or inactive": "NOT_FOUND_USER",
    "Job not found": "NOT_FOUND_JOB",
    "User not found": "NOT_FOUND_USER",
    "Application not found": "NOT_FOUND_APPLICATION",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = str(exc.detail) if exc.detail else "An error occurred"
    code = _ERROR_CODE_MAP.get(detail, "SERVER_ERROR")

    if exc.status_code == 429:
        code = "RATE_LIMIT_EXCEEDED"
    elif exc.status_code == 403:
        code = _ERROR_CODE_MAP.get(detail, "FORBIDDEN_PERMISSION_DENIED")
    elif exc.status_code == 404:
        code = _ERROR_CODE_MAP.get(detail, "NOT_FOUND")
    elif exc.status_code == 401:
        code = _ERROR_CODE_MAP.get(detail, "AUTH_INVALID_CREDENTIALS")

    return _error_response(exc.status_code, code, detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(loc) for loc in err.get("loc", [])), "issue": err.get("msg", "")}
        for err in exc.errors()
    ]
    return _error_response(422, "VALIDATION_MISSING_FIELD", "Validation error", details)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _error_response(429, "RATE_LIMIT_EXCEEDED", "Too many requests, please slow down")


# ─── SlowAPI rate limits on auth endpoints ───────────────────────────────────
# Applied via decorator on individual routes. Global default: 1000/min per IP.
# Auth-specific limits are set on the auth router endpoints.


# ─── Routers — all under /api/v1 ────────────────────────────────────────────

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(admit_cards_router)
app.include_router(answer_keys_router)
app.include_router(results_router)
app.include_router(job_docs_public_router)
app.include_router(applications.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(job_docs_admin_router)
app.include_router(exams_public_router)
app.include_router(exams_admin_router)
