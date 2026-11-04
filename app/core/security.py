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
            referer = request.headers.get("referer")
            
            # Determine incoming request host (check reverse-proxy headers first)
            client_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or urlparse(str(request.base_url)).netloc
            if ":" in client_host:
                client_host = client_host.split(":")[0]

            if origin:
                origin_host = urlparse(origin).netloc
                if ":" in origin_host:
                    origin_host = origin_host.split(":")[0]
                if origin_host != client_host:
                    return JSONResponse(status_code=403, content={"detail": "CSRF verification failed (Origin mismatch)"})
            elif referer:
                referer_host = urlparse(referer).netloc
                if ":" in referer_host:
                    referer_host = referer_host.split(":")[0]
                if referer_host != client_host:
                    return JSONResponse(status_code=403, content={"detail": "CSRF verification failed (Referer mismatch)"})
                    
        return await call_next(request)
