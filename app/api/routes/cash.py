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
from app.utils.timezone import get_ist_now, get_ist_today_range, format_ist_iso, format_ist_time, format_ist_datetime
from app.core.config import SECRET_KEY
from app.core.security import pwd_context
from app.api.dependencies import get_current_user

router = APIRouter()
from app.core.templates import templates

@router.get("/api/admin/expenses/today/{shop_id}")
async def get_shop_expenses_today(shop_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    today_start, today_end = get_ist_today_range()
    
    expenses = db.query(CashTransaction).filter(
        CashTransaction.shopkeeper_id == shop_id,
        CashTransaction.transaction_type == 'OUT',
        CashTransaction.timestamp >= today_start,
        CashTransaction.timestamp <= today_end
    ).order_by(CashTransaction.timestamp.desc()).all()
    
    return [
        {
            "id": exp.id,
            "amount": exp.amount,
            "reason": exp.description,
            "timestamp": format_ist_time(exp.timestamp)
        } for exp in expenses
    ]

@router.get("/api/cash-transactions")
async def get_cash_transactions(request: Request, shopkeeper_id: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shopkeeper_id = shopkeeper_id or user.id
    if user.role in ["Shopkeeper", "Factory"]:
        target_shopkeeper_id = user.id
        
    ist_now = get_ist_now()
    today_start, today_end = get_ist_today_range()
    
    # Get today's transactions in IST range
    transactions = db.query(CashTransaction).filter(
        CashTransaction.shopkeeper_id == target_shopkeeper_id,
        CashTransaction.timestamp >= today_start,
        CashTransaction.timestamp <= today_end
    ).order_by(CashTransaction.timestamp.desc()).all()
    
    # Get today's cash sales in IST range
    cash_sales = db.query(func.sum(Bill.final_amount)).filter(
        Bill.cashier_id == target_shopkeeper_id,
        Bill.payment_mode == "Cash",
        Bill.is_cancelled == False,
        Bill.timestamp >= today_start,
        Bill.timestamp <= today_end
    ).scalar() or 0.0
    
    total_in = sum([t.amount for t in transactions if t.transaction_type == "IN"])
    total_out = sum([t.amount for t in transactions if t.transaction_type == "OUT"])
    
    current_cash_balance = cash_sales + total_in - total_out
    
    result = []
    for t in transactions:
        can_revert = False
        if t.timestamp:
            elapsed = (ist_now - t.timestamp).total_seconds()
            # 5-minute revert window (300 seconds) with 30s grace for slight clock variations
            can_revert = (-30 <= elapsed <= 300)

        result.append({
            "id": t.id,
            "amount": t.amount,
            "type": t.transaction_type,
            "description": t.description,
            "timestamp": format_ist_iso(t.timestamp),
            "formatted_time": format_ist_datetime(t.timestamp),
            "time_display": format_ist_time(t.timestamp),
            "can_revert": can_revert
        })
        
    return {
        "status": "success", 
        "transactions": result, 
        "balance": current_cash_balance,
        "cash_sales": cash_sales,
        "total_in": total_in,
        "total_out": total_out
    }

@router.post("/api/cash-transactions")
async def add_cash_transaction(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shopkeeper_id = data.get("shopkeeper_id") or user.id
    if user.role in ["Shopkeeper", "Factory"]:
        target_shopkeeper_id = user.id
        
    amount = float(data.get("amount", 0))
    transaction_type = data.get("type", "IN")
    description = data.get("description", "")
    
    if amount <= 0:
        return JSONResponse(status_code=400, content={"detail": "Amount must be greater than 0"})
        
    ist_now = get_ist_now()
    new_tx = CashTransaction(
        shopkeeper_id=target_shopkeeper_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        timestamp=ist_now
    )
    
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    
    return {
        "status": "success", 
        "transaction_id": new_tx.id,
        "timestamp": format_ist_iso(new_tx.timestamp),
        "formatted_time": format_ist_datetime(new_tx.timestamp)
    }

async def _perform_cash_revert(request: Request, transaction_id: int, db: Session):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner", "Factory"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    tx = db.query(CashTransaction).filter(CashTransaction.id == transaction_id).first()
    if not tx:
        return JSONResponse(status_code=404, content={"detail": "Transaction not found"})
        
    if user.role in ["Shopkeeper", "Factory"] and tx.shopkeeper_id != user.id:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized: You can only revert your own transactions."})
        
    # Check 5-minute window in IST
    if tx.timestamp:
        ist_now = get_ist_now()
        elapsed = (ist_now - tx.timestamp).total_seconds()
        if elapsed > 300:
            return JSONResponse(status_code=400, content={"detail": "Cannot revert transaction after 5 minutes."})
    
    db.delete(tx)
    db.commit()
    return {"status": "success", "success": True, "detail": "Transaction reverted."}

@router.delete("/api/cash-transactions/{transaction_id}")
async def delete_cash_transaction(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    return await _perform_cash_revert(request, transaction_id, db)

@router.post("/api/cash-transactions/{transaction_id}/revert")
async def revert_cash_transaction(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    return await _perform_cash_revert(request, transaction_id, db)
