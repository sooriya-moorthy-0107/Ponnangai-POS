from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
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
from app.core.templates import templates

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
        
    # Get last 20 bills with eager-loaded items and products (prevents N+1 queries)
    bills = (
        query.options(joinedload(Bill.items).joinedload(BillItem.product))
        .order_by(Bill.timestamp.desc())
        .limit(20)
        .all()
    )
    
    if not bills:
        return {"status": "success", "bills": []}

    cashier_ids = list({b.cashier_id for b in bills if b.cashier_id})
    bill_ids = [b.id for b in bills]

    # Efficiently calculate bill numbers in 1 query using SQL window function
    bill_num_map = {}
    try:
        subq = db.query(
            Bill.id,
            func.row_number().over(partition_by=Bill.cashier_id, order_by=Bill.id).label("seq")
        ).filter(Bill.cashier_id.in_(cashier_ids)).subquery()
        rows = db.query(subq.c.id, subq.c.seq).filter(subq.c.id.in_(bill_ids)).all()
        bill_num_map = dict(rows)
    except Exception:
        # Fallback if window functions not supported in older dialect
        pass

    result = []
    for b in bills:
        bill_number = bill_num_map.get(b.id)
        if bill_number is None:
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
    
    bill = (
        db.query(Bill)
        .options(joinedload(Bill.items).joinedload(BillItem.product))
        .filter(Bill.id == bill_id)
        .first()
    )
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
        
    items_data = data.get("items", [])
    if not items_data:
        return JSONResponse(status_code=400, content={"detail": "Cart is empty"})

    # Extract item IDs and bulk-query all Products and ShopInventories in just 2 queries
    product_ids = [int(item["id"]) for item in items_data if "id" in item]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    prod_map = {p.id: p for p in products}

    shop_invs = db.query(ShopInventory).filter(
        ShopInventory.shopkeeper_id == target_shopkeeper_id,
        ShopInventory.product_id.in_(product_ids)
    ).all()
    inv_map = {inv.product_id: inv for inv in shop_invs}

    # Pass 1: Validate available stock in memory
    for item in items_data:
        pid = int(item["id"])
        product = prod_map.get(pid)
        if not product:
            continue
            
        current_stock = inv_map[pid].stock if pid in inv_map else 0
        qty_requested = float(item["qty"])
        if sk_user.role != "Factory" and current_stock < qty_requested:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Insufficient stock for '{product.name}'. Only {current_stock} left, but {qty_requested} were requested."}
            )
            
    # Pass 2: Deduct stock and compile bill items
    total_amount = 0.0
    bill_items = []
    
    for item in items_data:
        pid = int(item["id"])
        product = prod_map.get(pid)
        if not product:
            continue
            
        qty_float = float(item["qty"])
        custom_price = float(item.get("price", product.price))
        
        # Deduct from shop inventory
        if sk_user.role != "Factory" and pid in inv_map:
            inv_map[pid].stock -= int(qty_float)
            
        line_total = custom_price * qty_float
        total_amount += line_total
        
        b_item = BillItem(
            product_id=product.id,
            quantity=qty_float,
            price_at_sale=custom_price,
            packaging_type=item.get("packaging_type", "bottle"),
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
        cashier_name=cashier_name,
        items=bill_items
    )
    
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    
    return {"status": "success", "bill_id": new_bill.id}

@router.post("/api/bills/{bill_id}/revert")
async def revert_bill(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    bill = (
        db.query(Bill)
        .options(joinedload(Bill.items).joinedload(BillItem.product))
        .filter(Bill.id == bill_id)
        .first()
    )
    if not bill:
        return JSONResponse(status_code=404, content={"detail": "Bill not found"})
        
    cashier = db.query(User).filter(User.id == bill.cashier_id).first()
    is_factory = cashier and cashier.role == "Factory"
        
    item_product_ids = [item.product_id for item in bill.items]
    shop_invs = db.query(ShopInventory).filter(
        ShopInventory.shopkeeper_id == bill.cashier_id,
        ShopInventory.product_id.in_(item_product_ids)
    ).all()
    inv_map = {inv.product_id: inv for inv in shop_invs}

    items_data = []
    # Revert stock and prepare cart data
    for item in bill.items:
        max_stock = 9999.0
        if not is_factory and item.product_id in inv_map:
            inv_map[item.product_id].stock += int(item.quantity)
            max_stock = float(inv_map[item.product_id].stock)
            
        items_data.append({
            "id": item.product.id if item.product else item.product_id,
            "name": item.product.name if item.product else "Item",
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
