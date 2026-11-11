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
from app.utils.timezone import get_ist_today_range
from app.core.config import SECRET_KEY, SUPABASE_STORAGE_URL
from app.core.security import pwd_context
from app.api.dependencies import get_current_user

router = APIRouter()
from app.core.templates import templates

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if user.role == "Shopkeeper":
        return RedirectResponse(url="/shop", status_code=status.HTTP_302_FOUND)
    elif user.role == "Factory":
        return RedirectResponse(url="/factory", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.get("/shop", response_class=HTMLResponse)
async def shop_page(request: Request, shopkeeper_id: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Get active shopkeepers list
    shopkeepers = db.query(User).filter(User.role == "Shopkeeper", User.is_deleted == False).all()
    
    # Determine which shopkeeper's inventory to show
    if user.role == "Shopkeeper":
        target_shopkeeper_id = user.id
    else:
        if shopkeeper_id:
            target_shopkeeper_id = int(shopkeeper_id)
        elif shopkeepers:
            target_shopkeeper_id = shopkeepers[0].id
        else:
            target_shopkeeper_id = user.id

    # Fetch active products with their shop inventory in a single joined query
    rows = (
        db.query(Product, func.coalesce(ShopInventory.stock, 0).label("stock"))
        .outerjoin(
            ShopInventory,
            (ShopInventory.product_id == Product.id) & (ShopInventory.shopkeeper_id == target_shopkeeper_id)
        )
        .filter(
            Product.shopkeeper_id == target_shopkeeper_id,
            Product.is_deleted == False
        )
        .order_by(Product.id.asc())
        .all()
    )
    products = []
    for prod, stock_qty in rows:
        prod.stock = stock_qty
        products.append(prod)
    products.sort(key=lambda p: (get_product_sort_key(p.name), p.id))
        
    target_sk = db.query(User).filter(User.id == target_shopkeeper_id).first()
    target_sk_name = target_sk.username if target_sk else "Unknown Shop"
        
    return templates.TemplateResponse(request=request, name="shop.html", context={
        "request": request,
        "user": user,
        "products": products,
        "shopkeepers": shopkeepers,
        "target_shopkeeper_id": target_shopkeeper_id,
        "target_sk_name": target_sk_name,
        "storage_url": SUPABASE_STORAGE_URL
    })

@router.get("/factory", response_class=HTMLResponse)
async def factory_pos_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Factory", "Admin", "Manager", "Owner"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    target_cashier_id = user.id
    # Admin/Manager/Owner can view the POS of any Factory cashier, defaults to the first active Factory user
    if user.role in ["Admin", "Manager", "Owner"]:
        first_factory = db.query(User).filter(User.role == "Factory", User.is_deleted == False).first()
        target_cashier_id = first_factory.id if first_factory else user.id

    # Fetch products active for this factory cashier
    products = (
        db.query(Product)
        .filter(
            Product.shopkeeper_id == target_cashier_id,
            Product.is_deleted == False
        )
        .order_by(Product.id.asc())
        .all()
    )
    products.sort(key=lambda p: (get_product_sort_key(p.name), p.id))
    
    liquid_products = []
    solid_products = []
    for p in products:
        if p.product_type == "liquid":
            liquid_products.append(p)
        else:
            solid_products.append(p)
            
    target_cashier = db.query(User).filter(User.id == target_cashier_id).first()
    cashier_name = target_cashier.username if target_cashier else "Factory"
    
    users = db.query(User).filter(User.is_deleted == False).all()
    shopkeepers = [u for u in users if u.role in ["Shopkeeper", "Factory"]]
    
    return templates.TemplateResponse(request=request, name="factory_pos.html", context={
        "request": request,
        "user": user,
        "liquid_products": liquid_products,
        "solid_products": solid_products,
        "target_shopkeeper_id": target_cashier_id,
        "target_cashier_id": target_cashier_id,
        "cashier_name": cashier_name,
        "shopkeepers": shopkeepers,
        "storage_url": SUPABASE_STORAGE_URL
    })

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # Owner, Admin, Manager have access to the dashboard
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    products = (
        db.query(Product)
        .filter(Product.is_deleted == False)
        .order_by(Product.id.asc())
        .all()
    )
    products.sort(key=lambda p: (get_product_sort_key(p.name), p.id))
    # Filter out soft-deleted users/staff from active views
    users = db.query(User).filter(User.is_deleted == False).all()
    shopkeepers = [u for u in users if u.role in ["Shopkeeper", "Factory"]]
    
    # Load archived shopkeepers specifically for historical analytics
    archived_shopkeepers = db.query(User).filter(User.role.in_(["Shopkeeper", "Factory"]), User.is_deleted == True).all()
    
    # Inventory mapping: shop_inventory[shopkeeper_id][product_id] = stock
    all_inventory = db.query(ShopInventory).all()
    shop_inventory = {}
    for inv in all_inventory:
        if inv.shopkeeper_id not in shop_inventory:
            shop_inventory[inv.shopkeeper_id] = {}
        shop_inventory[inv.shopkeeper_id][inv.product_id] = inv.stock
        
    today_start, today_end = get_ist_today_range()
    
    # Dashboard metrics (Filtered for today)
    total_revenue = db.query(func.sum(Bill.final_amount)).filter(Bill.is_cancelled == False, Bill.timestamp >= today_start, Bill.timestamp <= today_end).scalar() or 0.0
    total_sales = db.query(Bill).filter(Bill.is_cancelled == False, Bill.timestamp >= today_start, Bill.timestamp <= today_end).count()
    total_expenses = db.query(func.sum(CashTransaction.amount)).filter(CashTransaction.transaction_type == 'OUT', CashTransaction.timestamp >= today_start, CashTransaction.timestamp <= today_end).scalar() or 0.0
    
    # Low stock alerts across active shops and active products (ignores soft-deleted stocks)
    low_stock_alerts = db.query(ShopInventory).join(Product).join(User, ShopInventory.shopkeeper_id == User.id).filter(
        ShopInventory.stock < 10,
        Product.is_deleted == False,
        User.is_deleted == False,
        User.role != "Factory"
    ).all()
    
    # Shop performance for active shopkeepers (All-time and Today) fetched via 3 aggregated queries instead of N+1 loops
    all_time_rows = (
        db.query(
            Bill.cashier_id,
            func.count(Bill.id).label("sales"),
            func.coalesce(func.sum(Bill.final_amount), 0.0).label("revenue")
        )
        .filter(Bill.is_cancelled == False)
        .group_by(Bill.cashier_id)
        .all()
    )
    all_time_map = {row.cashier_id: {"sales": row.sales, "revenue": float(row.revenue)} for row in all_time_rows}

    today_rows = (
        db.query(
            Bill.cashier_id,
            func.count(Bill.id).label("sales"),
            func.coalesce(func.sum(Bill.final_amount), 0.0).label("revenue")
        )
        .filter(Bill.is_cancelled == False, Bill.timestamp >= today_start, Bill.timestamp <= today_end)
        .group_by(Bill.cashier_id)
        .all()
    )
    today_map = {row.cashier_id: {"sales": row.sales, "revenue": float(row.revenue)} for row in today_rows}

    today_exp_rows = (
        db.query(
            CashTransaction.shopkeeper_id,
            func.coalesce(func.sum(CashTransaction.amount), 0.0).label("expenses")
        )
        .filter(CashTransaction.transaction_type == 'OUT', CashTransaction.timestamp >= today_start, CashTransaction.timestamp <= today_end)
        .group_by(CashTransaction.shopkeeper_id)
        .all()
    )
    today_exp_map = {row.shopkeeper_id: float(row.expenses) for row in today_exp_rows}

    shop_performance = []
    shop_performance_today = []
    for sk in shopkeepers:
        at = all_time_map.get(sk.id, {"sales": 0, "revenue": 0.0})
        td = today_map.get(sk.id, {"sales": 0, "revenue": 0.0})
        exp = today_exp_map.get(sk.id, 0.0)
        shop_performance.append({
            "shopkeeper": sk,
            "sales": at["sales"],
            "revenue": at["revenue"]
        })
        shop_performance_today.append({
            "shopkeeper": sk,
            "sales": td["sales"],
            "revenue": td["revenue"],
            "expenses": exp
        })
        
    return templates.TemplateResponse(request=request, name="admin.html", context={
        "request": request,
        "user": user,
        "products": products,
        "users": users,
        "shopkeepers": shopkeepers,
        "archived_shopkeepers": archived_shopkeepers,
        "shop_inventory": shop_inventory,
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "low_stock_alerts": low_stock_alerts,
        "shop_performance": shop_performance,
        "shop_performance_today": shop_performance_today,
        "archived_shopkeepers": archived_shopkeepers,
        "storage_url": SUPABASE_STORAGE_URL
    })

@router.get("/receipt/{bill_id}", response_class=HTMLResponse)
async def receipt_page(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    if user.role not in ["Admin", "Manager", "Owner"] and bill.cashier_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized: You cannot access receipts from another shop.")
        
    bill_number = db.query(Bill).filter(
        Bill.cashier_id == bill.cashier_id,
        Bill.id <= bill.id
    ).count()
        
    return templates.TemplateResponse(
        request=request, 
        name="receipt.html", 
        context={
            "request": request, 
            "bill": bill, 
            "bill_number": bill_number, 
            "user": user,
            "storage_url": SUPABASE_STORAGE_URL
        }
    )
