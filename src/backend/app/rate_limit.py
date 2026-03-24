"""SlowAPI rate limiter — shared instance used by routers and main app."""

from fastapi import Request
from slowapi import Limiter


def _get_real_ip(request: Request) -> str:
    """Return the real client IP, preferring X-Real-IP set by Nginx.

    Falls back to X-Forwarded-For, then the direct connection host.
    Without this, behind a reverse proxy all requests share the proxy IP
    and rate limits become global rather than per-client.
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_get_real_ip, default_limits=["1000/minute"])
