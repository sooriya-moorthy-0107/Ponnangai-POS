import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY, PRODUCTION
from app.core.security import CSRFMiddleware
from app.api.routes import auth, pages, billing, cash, inventory, products, users, reports, admin

app = FastAPI(title="Ponnangai POS")

# Middlewares
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    https_only=PRODUCTION,
    same_site="lax"
)
app.add_middleware(CSRFMiddleware)

# Static files
os.makedirs("photos", exist_ok=True)
os.makedirs("photos/wobg", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
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
