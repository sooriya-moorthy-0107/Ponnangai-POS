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

@router.post("/api/users/update_password")
async def update_password(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # ONLY Admin has full access to edit passwords
    if not user or user.role != "Admin":
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin can change passwords."})
        
    target_user_id = data.get("user_id")
    new_password = data.get("new_password")
    
    if not target_user_id or not new_password:
        return JSONResponse(status_code=400, content={"detail": "Missing user_id or new_password"})
        
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
        
    target_user.password = pwd_context.hash(new_password)
    db.commit()
    return {"status": "success", "detail": f"Password updated for {target_user.username}"}

@router.post("/api/users/add")
async def add_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role")
    
    if not username or not password or not role:
        return JSONResponse(status_code=400, content={"detail": "Missing required fields"})
        
    # Manager can only add Shopkeeper
    if user.role == "Manager" and role != "Shopkeeper":
        return JSONResponse(status_code=403, content={"detail": "Managers can only create Shopkeeper accounts"})
        
    existing_user = db.query(User).filter(User.username == username, User.is_deleted == False).first()
    if existing_user:
        return JSONResponse(status_code=400, content={"detail": "Username already exists"})
        
    new_user = User(username=username, password=pwd_context.hash(password), role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Every new shop starts from zero and doesn't auto-create zero-stock inventory records.
        
    return {"status": "success", "detail": f"{role} '{username}' created successfully"}

@router.post("/api/users/edit")
async def edit_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_id = data.get("user_id")
    new_username = data.get("username", "").strip() if data.get("username") else None
    new_role = data.get("role")
    
    if not target_id or not new_username or not new_role:
        return JSONResponse(status_code=400, content={"detail": "Missing fields"})
        
    target_user = db.query(User).filter(User.id == target_id).first()
    if not target_user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
        
    target_user.username = new_username
    target_user.role = new_role
    db.commit()
    return {"status": "success", "detail": "User updated"}

@router.post("/api/users/delete")
async def delete_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin/Owner can delete."})
        
    target_id = data.get("user_id")
    if target_id is None:
        return JSONResponse(status_code=400, content={"detail": "Missing user ID"})
    try:
        target_id = int(target_id)
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid user ID format"})
        
    target_user = db.query(User).filter(User.id == target_id, User.is_deleted == False).first()
    if not target_user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
        
    if target_user.id == user.id:
        return JSONResponse(status_code=400, content={"detail": "Cannot delete yourself"})
        
    # Soft delete: set is_deleted = True and rename to release unique constraint
    target_user.is_deleted = True
    original_username = target_user.username
    target_user.username = f"{original_username} (Archived - {datetime.now().strftime('%Y-%m-%d %H:%M')})"
    
    # Soft-delete all products of this shopkeeper so they are hidden from all active POS/admin views
    db.query(Product).filter(Product.shopkeeper_id == target_id).update({Product.is_deleted: True})
    
    # Set active stock of deleted shopkeeper products to 0 to prevent rogue stock alerts
    db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == target_id).update({ShopInventory.stock: 0})
    
    db.commit()
    return {"status": "success", "detail": f"User '{original_username}' successfully archived and deleted."}

@router.post("/api/users/hard_delete")
async def hard_delete_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "Admin":
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin can permanently delete."})
        
    target_id = data.get("user_id")
    if target_id is None:
        return JSONResponse(status_code=400, content={"detail": "Missing user ID"})
    try:
        target_id = int(target_id)
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid user ID format"})
        
    target_user = db.query(User).filter(User.id == target_id).first()
    if not target_user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
        
    if target_user.id == user.id:
        return JSONResponse(status_code=400, content={"detail": "Cannot permanently delete yourself"})
        
    # Find all bills by this cashier
    bills = db.query(Bill.id).filter(Bill.cashier_id == target_id).all()
    bill_ids = [b[0] for b in bills]
    
    # Delete BillItems for these bills
    if bill_ids:
        db.query(BillItem).filter(BillItem.bill_id.in_(bill_ids)).delete(synchronize_session=False)
        db.query(Bill).filter(Bill.id.in_(bill_ids)).delete(synchronize_session=False)

    # Now, find all products by this shopkeeper
    products = db.query(Product.id).filter(Product.shopkeeper_id == target_id).all()
    product_ids = [p[0] for p in products]

    if product_ids:
        # Delete any remaining BillItems that reference these products
        db.query(BillItem).filter(BillItem.product_id.in_(product_ids)).delete(synchronize_session=False)
        # Delete ShopInventory for these products
        db.query(ShopInventory).filter(ShopInventory.product_id.in_(product_ids)).delete(synchronize_session=False)
        # Delete the products themselves
        db.query(Product).filter(Product.id.in_(product_ids)).delete(synchronize_session=False)

    # Delete CashTransactions
    db.query(CashTransaction).filter(CashTransaction.shopkeeper_id == target_id).delete(synchronize_session=False)
    # Delete ShopInventory explicitly by shopkeeper_id (just in case)
    db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == target_id).delete(synchronize_session=False)
    
    db.delete(target_user)
    db.commit()
    
    return {"status": "success", "detail": "User and all associated history permanently deleted."}

