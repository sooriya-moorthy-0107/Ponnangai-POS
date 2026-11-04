import time
import threading
from collections import defaultdict, deque
from urllib.parse import urlparse
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import PRODUCTION

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class InMemoryRateLimiter:
    """Thread-safe in-memory rate limiter with sliding window."""
    def __init__(self):
        self._records = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int = 5, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            history = self._records[key]
            # Expire old records outside the current window
            while history and history[0] <= now - window_seconds:
                history.popleft()

            if len(history) >= max_requests:
                earliest = history[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                return False, retry_after

            history.append(now)
            return True, 0

    def cleanup(self, max_idle: int = 3600):
        """Periodically prune keys that haven't been active."""
        now = time.time()
        with self._lock:
            keys_to_delete = [
                k for k, timestamps in self._records.items()
                if not timestamps or timestamps[-1] <= now - max_idle
            ]
            for k in keys_to_delete:
                del self._records[k]


# Global rate limiter instance
login_rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Safely determine client IP from forward headers or client host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP is the original client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds essential security headers to block XSS, clickjacking, and MIME sniffing."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Standard defense-in-depth headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (allows necessary inline scripts, google fonts, and sweetalert/cdn)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'self';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Force HTTPS / HSTS in production
        if PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Enforces origin/referer validation on mutating requests."""
    EXEMPT_PATHS = {"/api/auth/invalidate-session"}

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if request.url.path in self.EXEMPT_PATHS:
                return await call_next(request)

            origin = request.headers.get("origin")
            referer = request.headers.get("referer")

            # Determine incoming request host (check reverse-proxy headers first)
            client_host = (
                request.headers.get("x-forwarded-host")
                or request.headers.get("host")
                or urlparse(str(request.base_url)).netloc
            )
            if ":" in client_host:
                client_host = client_host.split(":")[0]

            if origin:
                origin_host = urlparse(origin).netloc
                if ":" in origin_host:
                    origin_host = origin_host.split(":")[0]
                if origin_host != client_host:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF verification failed (Origin mismatch)"}
                    )
            elif referer:
                referer_host = urlparse(referer).netloc
                if ":" in referer_host:
                    referer_host = referer_host.split(":")[0]
                if referer_host != client_host:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF verification failed (Referer mismatch)"}
                    )
            elif PRODUCTION:
                # In production, state-changing requests without Origin or Referer are rejected
                sec_fetch_site = request.headers.get("sec-fetch-site")
                if sec_fetch_site and sec_fetch_site not in ["same-origin", "same-site"]:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF verification failed (Cross-site request blocked)"}
                    )

        return await call_next(request)
