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

@router.get("/api/bills/history")
async def get_bill_history(request: Request, shopkeeper_id: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    query = db.query(Bill)
    if user.role == "Shopkeeper":
        query = query.filter(Bill.cashier_id == user.id)
    elif shopkeeper_id:
        query = query.filter(Bill.cashier_id == shopkeeper_id)
        
    # Get last 20 bills
    bills = query.order_by(Bill.timestamp.desc()).limit(20).all()
    
    result = []
    for b in bills:
        bill_number = db.query(Bill).filter(
            Bill.cashier_id == b.cashier_id,
            Bill.id <= b.id
        ).count()
        items = []
        for item in b.items:
            items.append({
                "product_id": item.product_id,
                "name": item.product.name if item.product else "Deleted Item",
                "quantity": item.quantity,
                "price": item.price_at_sale,
                "total": item.price_at_sale * item.quantity,
                "packaging_type": item.packaging_type,
                "bottle_type": item.bottle_type
            })
            
        result.append({
            "id": b.id,
            "bill_number": bill_number,
            "total_amount": b.total_amount,
            "discount": b.discount,
            "final_amount": b.final_amount,
            "payment_mode": b.payment_mode,
            "timestamp": b.timestamp.strftime('%Y-%m-%d %H:%M'),
            "cashier_name": b.cashier_name,
            "is_cancelled": b.is_cancelled,
            "items": items
        })
        
    return {"status": "success", "bills": result}

@router.get("/api/bills/{bill_id}")
async def get_bill_details(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
    
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return JSONResponse(status_code=404, content={"detail": "Bill not found"})
        
    bill_number = db.query(Bill).filter(
        Bill.cashier_id == bill.cashier_id,
        Bill.id <= bill.id
    ).count()
        
    items = []
    for item in bill.items:
        items.append({
            "product_id": item.product_id,
            "name": item.product.name if item.product else "Deleted Item",
            "quantity": item.quantity,
            "price": item.price_at_sale,
            "total": item.price_at_sale * item.quantity,
            "packaging_type": item.packaging_type,
            "bottle_type": item.bottle_type
        })
        
    return {
        "status": "success",
        "bill": {
            "id": bill.id,
            "bill_number": bill_number,
            "total_amount": bill.total_amount,
            "discount": bill.discount,
            "final_amount": bill.final_amount,
            "payment_mode": bill.payment_mode,
            "timestamp": bill.timestamp.strftime('%Y-%m-%d %H:%M'),
            "cashier_name": bill.cashier_name,
            "is_cancelled": bill.is_cancelled,
            "items": items
        }
    }

@router.post("/api/bills")
async def create_bill(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shopkeeper_id = data.get("shopkeeper_id") or user.id
    if target_shopkeeper_id:
        target_shopkeeper_id = int(target_shopkeeper_id)
        
    sk_user = db.query(User).filter(User.id == target_shopkeeper_id, User.is_deleted == False).first()
    if not sk_user:
        return JSONResponse(status_code=400, content={"detail": "Invalid active cashier"})
        
    # Expected payload: {"items": [{"id": 1, "qty": 2.5}], "discount": 10.0, "payment_mode": "Cash"}
    total_amount = 0.0
    bill_items = []
    
    # Pass 1: Validate available stock for all items
    for item in data.get("items", []):
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            continue
            
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == target_shopkeeper_id,
            ShopInventory.product_id == product.id
        ).first()
        
        current_stock = shop_inv.stock if shop_inv else 0
        if sk_user.role != "Factory" and current_stock < item["qty"]:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Insufficient stock for '{product.name}'. Only {current_stock} left, but {item['qty']} were requested."}
            )
            
    # Pass 2: Deduct stock and compile bill items
    for item in data.get("items", []):
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            continue
            
        qty_float = float(item["qty"])
        custom_price = float(item.get("price", product.price))
        
        # Standard Shopkeeper: deduct from traditional inventory
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == target_shopkeeper_id, 
            ShopInventory.product_id == product.id
        ).first()
        if shop_inv and sk_user.role != "Factory":
            shop_inv.stock -= int(item["qty"])
            
        line_total = custom_price * qty_float
        total_amount += line_total
        
        b_item = BillItem(
            product_id=product.id,
            quantity=qty_float,
            price_at_sale=custom_price,
            packaging_type=item.get("packaging_type", "bottle"), # default bottle for shops
            bottle_type=item.get("bottle_type", None),
            bottle_count=int(item.get("bottle_count", 0))
        )
        bill_items.append(b_item)
        
    discount = float(data.get("discount", 0.0))
    raw_final = max(0.0, total_amount - discount)
    final_amount = float(round(raw_final))
    round_off = final_amount - raw_final
    
    cashier_name = sk_user.username
    if user.id != sk_user.id:
        cashier_name = f"{sk_user.username} ({user.username})"
    
    new_bill = Bill(
        total_amount=total_amount,
        discount=discount,
        final_amount=final_amount,
        round_off=round_off,
        payment_mode=data.get("payment_mode", "Cash"),
        cashier_id=target_shopkeeper_id,
        cashier_name=cashier_name
    )
    
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    
    for b_item in bill_items:
        b_item.bill_id = new_bill.id
        db.add(b_item)
        
    db.commit()
    
    return {"status": "success", "bill_id": new_bill.id}

@router.post("/api/bills/{bill_id}/revert")
async def revert_bill(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return JSONResponse(status_code=404, content={"detail": "Bill not found"})
        
    cashier = db.query(User).filter(User.id == bill.cashier_id).first()
    is_factory = cashier and cashier.role == "Factory"
        
    items_data = []
    # Revert stock and prepare cart data
    for item in bill.items:
        max_stock = 9999.0 # Default fallback for loose sales in UI
        # Restore stock in shop inventory
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == bill.cashier_id,
            ShopInventory.product_id == item.product_id
        ).first()
        if shop_inv and not is_factory:
            shop_inv.stock += int(item.quantity)
            max_stock = float(shop_inv.stock)
            
        items_data.append({
            "id": item.product.id,
            "name": item.product.name,
            "price": item.price_at_sale,
            "qty": item.quantity,
            "maxStock": max_stock
        })
        
    discount = bill.discount
    payment_mode = bill.payment_mode
    
    # Mark the bill as cancelled in database
    bill.is_cancelled = True
    db.commit()
    
    return {
        "status": "success", 
        "items": items_data,
        "discount": discount,
        "payment_mode": payment_mode
    }

