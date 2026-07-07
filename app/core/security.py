from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from urllib.parse import urlparse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            origin = request.headers.get("origin")
            if origin:
                origin_parsed = urlparse(origin)
                host_parsed = urlparse(str(request.base_url))
                if origin_parsed.netloc != host_parsed.netloc:
                    return JSONResponse(status_code=403, content={"detail": "CSRF verification failed (Origin mismatch)"})
            # Also check referer if origin is missing
            referer = request.headers.get("referer")
            if not origin and referer:
                referer_parsed = urlparse(referer)
                host_parsed = urlparse(str(request.base_url))
                if referer_parsed.netloc != host_parsed.netloc:
                    return JSONResponse(status_code=403, content={"detail": "CSRF verification failed (Referer mismatch)"})
        return await call_next(request)
