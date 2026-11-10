import os
import sys
import logging
import traceback
import html
import time

# Enforce Indian Standard Time (IST) on server runtime
os.environ["TZ"] = "Asia/Kolkata"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

# Ensure base directory and lib directory are in sys.path and set as current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
for lib_cand in [os.path.join(BASE_DIR, "lib"), os.path.abspath("lib")]:
    if os.path.isdir(lib_cand) and lib_cand not in sys.path:
        sys.path.insert(0, lib_cand)
try:
    if os.getcwd() != BASE_DIR:
        os.chdir(BASE_DIR)
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import SECRET_KEY, PRODUCTION, SUPABASE_STORAGE_URL
from app.core.security import CSRFMiddleware, SecurityHeadersMiddleware
from app.models.database import Base, engine
import app.models.domain  # noqa: F401 - ensure models are registered
from app.api.routes import auth, pages, billing, cash, inventory, products, users, reports, admin

# Initialize database schema (creates tables on Supabase/PostgreSQL if they don't exist)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.getLogger("uvicorn.error").warning(f"Database schema initialization skipped: {e}")

# Disable Swagger & Redoc in production to prevent schema disclosure
app = FastAPI(
    title="Ponnangai POS",
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json"
)

# Global Exception Handler (prevents sensitive trace leak in production & blocks reflected XSS)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logging.error(f"Unhandled error on {request.url.path}: {exc}\n{error_trace}")
    
    if PRODUCTION:
        return HTMLResponse(
            content="""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Error - Ponnangai POS</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;padding:48px 24px;text-align:center;background:#F7FAFC;color:#2D3748;">
    <div style="max-width:480px;margin:0 auto;background:#FFF;padding:32px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);border:1px solid #E2E8F0;">
        <h2 style="color:#E53E3E;margin-top:0;">Server Error (500)</h2>
        <p style="color:#4A5568;line-height:1.6;">An unexpected error occurred while processing your request. Please try again or contact your administrator.</p>
        <a href="/" style="display:inline-block;margin-top:16px;background:#3182CE;color:#FFF;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">Return Home</a>
    </div>
</body>
</html>""",
            status_code=500
        )

    # In development mode, escape variables to prevent reflected XSS
    safe_type = html.escape(type(exc).__name__)
    safe_msg = html.escape(str(exc))
    safe_trace = html.escape(error_trace)
    return HTMLResponse(
        content=f"<html><body style='font-family:sans-serif;padding:24px;background:#FFF5F5;color:#9B2C2C;'>"
                f"<h2>Application Error (500)</h2>"
                f"<p><b>{safe_type}:</b> {safe_msg}</p>"
                f"<pre style='background:#FFF;padding:16px;border-radius:8px;border:1px solid #FEB2B2;overflow:auto;font-size:12px;color:#2D3748;'>{safe_trace}</pre>"
                f"</body></html>",
        status_code=500
    )

# Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    max_age=86400,  # 24-hour session expiry
    https_only=PRODUCTION,
    same_site="lax"
)
app.add_middleware(CSRFMiddleware)

# Static files
try:
    os.makedirs("photos", exist_ok=True)
    os.makedirs("photos/wobg", exist_ok=True)
except Exception:
    pass

app.mount("/static", StaticFiles(directory="static"), name="static")

# Photo Handler: Serves local files if present; otherwise redirects to Supabase Cloud Storage
@app.get("/photos/{filename:path}")
async def get_photo(filename: str):
    # 1. Local disk file check (for local development or Docker)
    local_path = os.path.join("photos", filename)
    if os.path.isfile(local_path):
        return FileResponse(local_path, headers={"Cache-Control": "public, max-age=604800, immutable"})
    
    # 2. Check in photos/wobg/
    wobg_path = os.path.join("photos", "wobg", filename)
    if os.path.isfile(wobg_path):
        return FileResponse(wobg_path, headers={"Cache-Control": "public, max-age=604800, immutable"})

    # 3. Supabase Cloud Storage Public Bucket
    if SUPABASE_STORAGE_URL:
        return RedirectResponse(
            url=f"{SUPABASE_STORAGE_URL}/{filename}",
            status_code=301,
            headers={"Cache-Control": "public, max-age=31536000, immutable"}
        )

    # 4. Fallback placeholder if not found
    placeholder = os.path.join("static", "images", "no-image.png")
    if os.path.isfile(placeholder):
        return FileResponse(placeholder, headers={"Cache-Control": "public, max-age=604800, immutable"})
    return Response(status_code=404)

# Include Routers
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(billing.router)
app.include_router(cash.router)
app.include_router(inventory.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=not PRODUCTION)
