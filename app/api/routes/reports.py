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

@router.get("/api/reports/daily")
async def get_daily_report(request: Request, shopkeeper_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})

    try:
        t_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        t_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    # Fetch bills for this shopkeeper in the date range (inclusive)
    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_role = shop.role if shop else "Shopkeeper"

    bottle_counts = {}
    report_data = {}
    for bill in bills:
        for item in bill.items:
            if item.packaging_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"] and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.bottle_count or item.quantity)
            product_name = item.product.name if item.product else "Unknown Product"
            pkg_type = item.packaging_type or "loose"
            btl_type = item.bottle_type or "N/A"
            
            key = (product_name, pkg_type, btl_type)
            if key not in report_data:
                report_data[key] = {
                    "product": product_name,
                    "packaging": pkg_type,
                    "bottle_type": btl_type if pkg_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"] else "N/A",
                    "total_quantity": 0.0,
                    "total_revenue": 0.0,
                    "bottle_count": 0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)
            if pkg_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"]:
                report_data[key]["bottle_count"] += (item.bottle_count or 0)

    revenue_breakdown = {
        "Cash": 0.0,
        "UPI": 0.0,
        "Card": 0.0,
        "Total": 0.0
    }
    for bill in bills:
        mode = bill.payment_mode or "Cash"
        if mode not in revenue_breakdown:
            revenue_breakdown[mode] = 0.0
        revenue_breakdown[mode] += bill.final_amount
        revenue_breakdown["Total"] += bill.final_amount

    results = list(report_data.values())
    # Sort for better presentation
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    total_cash_in = 0.0
    total_cash_out = 0.0
    all_cash_tx = db.query(CashTransaction).filter(CashTransaction.shopkeeper_id == shopkeeper_id).all()
    for tx in all_cash_tx:
        if tx.timestamp:
            tx_date = tx.timestamp.date()
            if t_start <= tx_date <= t_end:
                if tx.transaction_type == 'IN':
                    total_cash_in += tx.amount
                elif tx.transaction_type == 'OUT':
                    total_cash_out += tx.amount
            
    return {
        "status": "success", 
        "data": results, 
        "shop_role": shop_role, 
        "bottle_counts": bottle_counts, 
        "revenue_breakdown": revenue_breakdown,
        "total_cash_in": total_cash_in,
        "total_cash_out": total_cash_out
    }

@router.get("/api/reports/daily/export")
async def export_daily_report(request: Request, shopkeeper_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    if user.role not in ["Admin", "Manager", "Owner"]:
        if user.role in ["Shopkeeper", "Factory"]:
            if user.id != shopkeeper_id:
                return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        else:
            return JSONResponse(status_code=403, content={"detail": "Unauthorized"})

    try:
        t_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        t_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_name = shop.username if shop else "Unknown"

    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()

    report_data = {}
    total_sales = 0.0
    bottle_counts = {}
    for bill in bills:
        for item in bill.items:
            if item.packaging_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"] and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.bottle_count or item.quantity)
            product_name = item.product.name if item.product else "Unknown Product"
            pkg_type = item.packaging_type or "loose"
            btl_type = item.bottle_type or "N/A"
            
            key = (product_name, pkg_type, btl_type)
            if key not in report_data:
                report_data[key] = {
                    "product": product_name,
                    "packaging": pkg_type,
                    "bottle_type": btl_type if pkg_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"] else "N/A",
                    "total_quantity": 0.0,
                    "total_revenue": 0.0,
                    "bottle_count": 0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)
            if pkg_type in ["bottle", "1ltr", "5ltr", "1/2 ltr"]:
                report_data[key]["bottle_count"] += (item.bottle_count or 0)
            total_sales += (item.quantity * item.price_at_sale)

    revenue_breakdown = {
        "Cash": 0.0,
        "UPI": 0.0,
        "Card": 0.0,
        "Total": 0.0
    }
    for bill in bills:
        mode = bill.payment_mode or "Cash"
        if mode not in revenue_breakdown:
            revenue_breakdown[mode] = 0.0
        revenue_breakdown[mode] += bill.final_amount
        revenue_breakdown["Total"] += bill.final_amount

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Daily Sales Report"])
    writer.writerow(["Shop:", shop_name])
    writer.writerow(["Date Range:", f"{t_start.strftime('%Y-%m-%d')} to {t_end.strftime('%Y-%m-%d')}"])
    writer.writerow([])
    
    results = list(report_data.values())
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    total_cash_in = 0.0
    total_cash_out = 0.0
    all_cash_tx = db.query(CashTransaction).filter(CashTransaction.shopkeeper_id == shopkeeper_id).all()
    for tx in all_cash_tx:
        if tx.timestamp:
            tx_date = tx.timestamp.date()
            if t_start <= tx_date <= t_end:
                if tx.transaction_type == 'IN':
                    total_cash_in += tx.amount
                elif tx.transaction_type == 'OUT':
                    total_cash_out += tx.amount
    
    if shop and shop.role == "Factory":
        writer.writerow(["Product Name", "Bottle Type", "Packaging Type", "Total Quantity Sold", "Bottle Count", "Total Revenue (Rs)"])
        for r in results:
            writer.writerow([r["product"], r["bottle_type"], r["packaging"], f"{r['total_quantity']:.2f}", str(r.get("bottle_count", 0)), f"{r['total_revenue']:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Revenue Summary", f"Rs {total_sales:.2f}"])
        writer.writerow([])
        writer.writerow(["Revenue Breakdown"])
        writer.writerow(["Cash", f"Rs {revenue_breakdown.get('Cash', 0.0):.2f}"])
        writer.writerow(["UPI", f"Rs {revenue_breakdown.get('UPI', 0.0):.2f}"])
        writer.writerow(["Card", f"Rs {revenue_breakdown.get('Card', 0.0):.2f}"])
        writer.writerow(["Total Revenue (Bills)", f"Rs {revenue_breakdown.get('Total', 0.0):.2f}"])
        writer.writerow(["Money IN", f"+Rs {total_cash_in:.2f}"])
        writer.writerow(["Money OUT (Expenses)", f"-Rs {total_cash_out:.2f}"])
        net_cash = revenue_breakdown.get('Cash', 0.0) + total_cash_in - total_cash_out
        writer.writerow(["Total After Expense (Cash in Drawer)", f"Rs {net_cash:.2f}"])
        writer.writerow([])
        writer.writerow(["Bottle Counts"])
        for b_type, count in bottle_counts.items():
            if count > 0:
                writer.writerow([b_type, count])
    else:
        writer.writerow(["Product Name", "Total Quantity Sold", "Total Revenue (Rs)"])
        shop_agg = {}
        for r in results:
            if r["product"] not in shop_agg:
                shop_agg[r["product"]] = {"qty": 0.0, "rev": 0.0}
            shop_agg[r["product"]]["qty"] += r["total_quantity"]
            shop_agg[r["product"]]["rev"] += r["total_revenue"]
        for prod, val in shop_agg.items():
            writer.writerow([prod, f"{val['qty']:.2f}", f"{val['rev']:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Revenue Summary", f"Rs {total_sales:.2f}"])
        writer.writerow([])
        writer.writerow(["Revenue Breakdown"])
        writer.writerow(["Cash", f"Rs {revenue_breakdown.get('Cash', 0.0):.2f}"])
        writer.writerow(["UPI", f"Rs {revenue_breakdown.get('UPI', 0.0):.2f}"])
        writer.writerow(["Card", f"Rs {revenue_breakdown.get('Card', 0.0):.2f}"])
        writer.writerow(["Total Revenue (Bills)", f"Rs {revenue_breakdown.get('Total', 0.0):.2f}"])
        writer.writerow(["Money IN", f"+Rs {total_cash_in:.2f}"])
        writer.writerow(["Money OUT (Expenses)", f"-Rs {total_cash_out:.2f}"])
        net_cash = revenue_breakdown.get('Cash', 0.0) + total_cash_in - total_cash_out
        writer.writerow(["Total After Expense (Cash in Drawer)", f"Rs {net_cash:.2f}"])
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Sales_Report_{shop_name}_{t_start.strftime("%Y-%m-%d")}_to_{t_end.strftime("%Y-%m-%d")}.csv"'
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

@router.get("/api/analytics/shop/{shop_id}")
async def get_shop_analytics(request: Request, shop_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shop = db.query(User).filter(User.id == shop_id).first()
    if not target_shop:
        return JSONResponse(status_code=404, content={"detail": "Shop not found"})
        
    bills = db.query(Bill).filter(Bill.cashier_id == shop_id, Bill.is_cancelled == False).all()
    total_sales = len(bills)
    total_revenue = sum(b.final_amount for b in bills)
    
    items_query = db.query(
        Product.name,
        func.sum(BillItem.quantity).label("total_qty"),
        func.sum(BillItem.quantity * BillItem.price_at_sale).label("total_revenue")
    ).join(BillItem, Product.id == BillItem.product_id)\
     .join(Bill, Bill.id == BillItem.bill_id)\
     .filter(Bill.cashier_id == shop_id, Bill.is_cancelled == False)\
     .group_by(Product.name).all()
     
    breakdown = [{"product_name": row[0], "qty": row[1], "revenue": row[2]} for row in items_query]
    
    return {
        "status": "success",
        "shop_name": target_shop.username,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "breakdown": breakdown
    }

@router.get("/api/analytics/shop/{shop_id}/today")
async def get_shop_analytics_today(request: Request, shop_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shop = db.query(User).filter(User.id == shop_id).first()
    if not target_shop:
        return JSONResponse(status_code=404, content={"detail": "Shop not found"})
        
    today_start = datetime.combine(datetime.today(), time.min)
    today_end = datetime.combine(datetime.today(), time.max)
        
    bills = db.query(Bill).filter(
        Bill.cashier_id == shop_id, 
        Bill.is_cancelled == False,
        Bill.timestamp >= today_start,
        Bill.timestamp <= today_end
    ).all()
    total_sales = len(bills)
    total_revenue = sum(b.final_amount for b in bills)
    
    items_query = db.query(
        Product.name,
        func.sum(BillItem.quantity).label("total_qty"),
        func.sum(BillItem.quantity * BillItem.price_at_sale).label("total_revenue")
    ).join(BillItem, Product.id == BillItem.product_id)\
     .join(Bill, Bill.id == BillItem.bill_id)\
     .filter(
        Bill.cashier_id == shop_id, 
        Bill.is_cancelled == False,
        Bill.timestamp >= today_start,
        Bill.timestamp <= today_end
     )\
     .group_by(Product.name).all()
     
    breakdown = [{"product_name": row[0], "qty": row[1], "revenue": row[2]} for row in items_query]
    
    return {
        "status": "success",
        "shop_name": target_shop.username + " (Today)",
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "breakdown": breakdown
    }

