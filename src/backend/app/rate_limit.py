"""SlowAPI rate limiter — shared instance used by routers and main app."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])
