import sys
import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update BillItem model
target_billitem = """class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False) # Changed from Integer to Float for loose quantity sales
    price_at_sale = Column(Float, nullable=False)

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")"""

replacement_billitem = """class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False) # Changed from Integer to Float for loose quantity sales
    price_at_sale = Column(Float, nullable=False)
    packaging_type = Column(String, default="loose") # loose, bottle
    bottle_type = Column(String, nullable=True) # Type 1, Type 2, Type 3

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")"""
content = content.replace(target_billitem, replacement_billitem)

# 2. Update DB Init block
target_dbinit = """try:
    if DATABASE_URL.startswith("sqlite:///"):
        db_init.execute(text("ALTER TABLE products ADD COLUMN shopkeeper_id INTEGER"))"""

replacement_dbinit = """try:
    if DATABASE_URL.startswith("sqlite:///"):
        db_init.execute(text("ALTER TABLE bill_items ADD COLUMN packaging_type TEXT DEFAULT 'loose'"))
    else:
        db_init.execute(text("ALTER TABLE bill_items ADD COLUMN packaging_type VARCHAR DEFAULT 'loose'"))
    db_init.commit()
except Exception:
    db_init.rollback()
    
try:
    if DATABASE_URL.startswith("sqlite:///"):
        db_init.execute(text("ALTER TABLE bill_items ADD COLUMN bottle_type TEXT"))
    else:
        db_init.execute(text("ALTER TABLE bill_items ADD COLUMN bottle_type VARCHAR"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    if DATABASE_URL.startswith("sqlite:///"):
        db_init.execute(text("ALTER TABLE products ADD COLUMN shopkeeper_id INTEGER"))"""
content = content.replace(target_dbinit, replacement_dbinit)

# 3. Update create_bill API (api/bills)
target_create_bill = """        b_item = BillItem(
            bill_id=new_bill.id,
            product_id=product.id,
            quantity=qty_float,
            price_at_sale=custom_price
        )"""

replacement_create_bill = """        b_item = BillItem(
            bill_id=new_bill.id,
            product_id=product.id,
            quantity=qty_float,
            price_at_sale=custom_price,
            packaging_type=item.get("packaging_type", "loose"),
            bottle_type=item.get("bottle_type", None)
        )"""
content = content.replace(target_create_bill, replacement_create_bill)

# 4. Add Report APIs
# Find a good place to insert them, e.g., right before: @app.post("/api/bills/{bill_id}/revert")
target_revert = """@app.post("/api/bills/{bill_id}/revert")"""

report_apis = """
from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/api/reports/daily")
async def get_daily_report(request: Request, shopkeeper_id: int, date: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})

    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    # Fetch bills for this shopkeeper on the specific date
    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) == target_date
    ).all()

    report_data = {}
    for bill in bills:
        for item in bill.items:
            product_name = item.product.name if item.product else "Unknown Product"
            pkg_type = item.packaging_type or "loose"
            btl_type = item.bottle_type or "N/A"
            
            key = (product_name, pkg_type, btl_type)
            if key not in report_data:
                report_data[key] = {
                    "product": product_name,
                    "packaging": pkg_type,
                    "bottle_type": btl_type if pkg_type == "bottle" else "N/A",
                    "total_quantity": 0.0,
                    "total_revenue": 0.0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)

    results = list(report_data.values())
    # Sort for better presentation
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    return {"status": "success", "data": results}

@app.get("/api/reports/daily/export")
async def export_daily_report(request: Request, shopkeeper_id: int, date: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})

    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_name = shop.username if shop else "Unknown"

    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) == target_date
    ).all()

    report_data = {}
    total_sales = 0.0
    for bill in bills:
        for item in bill.items:
            product_name = item.product.name if item.product else "Unknown Product"
            pkg_type = item.packaging_type or "loose"
            btl_type = item.bottle_type or "N/A"
            
            key = (product_name, pkg_type, btl_type)
            if key not in report_data:
                report_data[key] = {
                    "product": product_name,
                    "packaging": pkg_type,
                    "bottle_type": btl_type if pkg_type == "bottle" else "N/A",
                    "total_quantity": 0.0,
                    "total_revenue": 0.0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)
            total_sales += (item.quantity * item.price_at_sale)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Daily Sales Report"])
    writer.writerow(["Shop:", shop_name])
    writer.writerow(["Date:", target_date.strftime("%Y-%m-%d")])
    writer.writerow(["Total Revenue:", f"Rs {total_sales:.2f}"])
    writer.writerow([])
    writer.writerow(["Product Name", "Packaging Type", "Bottle Type", "Total Quantity Sold", "Total Revenue (Rs)"])
    
    results = list(report_data.values())
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    for r in results:
        writer.writerow([r["product"], r["packaging"], r["bottle_type"], f"{r['total_quantity']:.2f}", f"{r['total_revenue']:.2f}"])
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Daily_Report_{shop_name}_{target_date.strftime("%Y-%m-%d")}.csv"'
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

@app.post("/api/bills/{bill_id}/revert")"""
content = content.replace(target_revert, report_apis)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)
