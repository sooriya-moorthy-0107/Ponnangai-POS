import os
import sys
import logging
import traceback

# Ensure base directory is in sys.path and set as current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
try:
    if os.getcwd() != BASE_DIR:
        os.chdir(BASE_DIR)
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY, PRODUCTION
from app.core.security import CSRFMiddleware
from app.models.database import Base, engine
import app.models.domain  # noqa: F401 - ensure models are registered
from app.api.routes import auth, pages, billing, cash, inventory, products, users, reports, admin

# Initialize database schema (creates tables on Supabase/PostgreSQL if they don't exist)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.getLogger("uvicorn.error").warning(f"Database schema initialization skipped: {e}")

app = FastAPI(title="Ponnangai POS")

# Global Exception Handler (returns readable error trace if an unhandled crash occurs)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logging.error(f"Unhandled error on {request.url.path}: {exc}\n{error_trace}")
    return HTMLResponse(
        content=f"<html><body style='font-family:sans-serif;padding:24px;background:#FFF5F5;color:#9B2C2C;'>"
                f"<h2>Application Error (500)</h2>"
                f"<p><b>{type(exc).__name__}:</b> {str(exc)}</p>"
                f"<pre style='background:#FFF;padding:16px;border-radius:8px;border:1px solid #FEB2B2;overflow:auto;font-size:12px;color:#2D3748;'>{error_trace}</pre>"
                f"</body></html>",
        status_code=500
    )

# Middlewares
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
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
if os.path.exists("photos"):
    app.mount("/photos", StaticFiles(directory="photos"), name="photos")

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
