from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, date, time
from typing import List, Optional
import os, csv, io, uuid, secrets

from app.models.database import get_db
from app.models.domain import User, Product, ShopInventory, Bill, BillItem, CashTransaction
from app.utils.helpers import get_product_sort_key, clean_csv_val, parse_csv_int
from app.core.config import SECRET_KEY
from app.core.security import pwd_context
from app.api.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@router.post("/login")
async def do_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    username_clean = username.strip()
    user = db.query(User).filter(User.username == username_clean, User.is_deleted == False).first()
    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid username or password"})
    
    request.session["user_id"] = user.id
    
    if user.role == "Shopkeeper":
        return RedirectResponse(url="/shop", status_code=status.HTTP_302_FOUND)
    elif user.role == "Factory":
        return RedirectResponse(url="/factory", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

