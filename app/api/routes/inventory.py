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

@router.post("/api/inventory/update")
async def update_inventory(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product_id = data.get("id")
    new_stock = data.get("stock")
    shopkeeper_id = data.get("shopkeeper_id")
    
    if product_id is None or new_stock is None or shopkeeper_id is None:
        return JSONResponse(status_code=400, content={"detail": "Missing id, stock, or shopkeeper_id"})
        
    shop_inv = db.query(ShopInventory).filter(
        ShopInventory.shopkeeper_id == shopkeeper_id,
        ShopInventory.product_id == product_id
    ).first()
    
    if not shop_inv:
        # Create it if it doesn't exist
        shop_inv = ShopInventory(shopkeeper_id=shopkeeper_id, product_id=product_id, stock=int(new_stock))
        db.add(shop_inv)
    else:
        shop_inv.stock = int(new_stock)
        
    db.commit()
    return {"status": "success", "detail": "Stock updated successfully"}

@router.get("/api/inventory/data/{shopkeeper_id}")
async def get_shopkeeper_inventory_data(request: Request, shopkeeper_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner", "Shopkeeper", "Factory"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    if user.role == "Shopkeeper" and user.id != shopkeeper_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Shopkeepers can only access their own inventory data.")
        
    products = db.query(Product).filter(
        Product.shopkeeper_id == shopkeeper_id,
        Product.is_deleted == False
    ).all()
    products.sort(key=lambda p: get_product_sort_key(p.name))
    
    shop_invs = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper_id).all()
    inv_map = {inv.product_id: inv.stock for inv in shop_invs}
    
    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": inv_map.get(p.id, 0),
            "image_filename": p.image_filename,
            "product_type": p.product_type,
            "unit": p.unit
        })
        
    return {"status": "success", "products": data}

@router.get("/api/inventory/template/{shopkeeper_id}")
async def get_inventory_template(request: Request, shopkeeper_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner", "Shopkeeper"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    if user.role == "Shopkeeper" and user.id != shopkeeper_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Shopkeepers can only access their own inventory template.")
    
    # Query only active products scoped to this shopkeeper
    products = db.query(Product).filter(
        Product.shopkeeper_id == shopkeeper_id,
        Product.is_deleted == False
    ).all()
    products.sort(key=lambda p: get_product_sort_key(p.name))
    shop_invs = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper_id).all()
    inv_map = {inv.product_id: inv.stock for inv in shop_invs}
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["S.No.", "Product Name", "Current Stock", "New Stock"])
    
    for idx, p in enumerate(products, 1):
        writer.writerow([idx, p.name, inv_map.get(p.id, 0), ""])
        
    headers = {
        "Content-Disposition": f"attachment; filename=shop_{shopkeeper_id}_inventory_template.csv"
    }
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

@router.post("/api/inventory/bulk_upload")
async def bulk_upload_inventory(request: Request, shopkeeper_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner", "Shopkeeper"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    if user.role == "Shopkeeper" and user.id != shopkeeper_id:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized: Shopkeepers can only update their own inventory."})
    if not file.filename.endswith('.csv'):
        return JSONResponse(status_code=400, content={"detail": "File must be a CSV"})
        
    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig')
    except Exception:
        try:
            decoded = content.decode('utf-8')
        except Exception:
            try:
                decoded = content.decode('latin-1')
            except Exception:
                return JSONResponse(status_code=400, content={"detail": "Could not decode file. Ensure it is a valid CSV."})
                
    # Sniff CSV delimiter (comma vs semicolon vs tab vs pipe)
    first_line = ""
    for line in decoded.splitlines():
        if line.strip():
            first_line = line
            break
            
    delimiter = ','
    if first_line:
        delimiters = [',', ';', '\t', '|']
        counts = {d: first_line.count(d) for d in delimiters}
        best_delim = max(counts, key=counts.get)
        if counts[best_delim] > 0:
            delimiter = best_delim
            
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    
    updated_count = 0
    for row in reader:
        # Standardize keys by lowercasing and stripping special chars
        norm_row = {}
        for k, v in row.items():
            if k is not None:
                norm_key = str(k).strip().lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
                norm_row[norm_key] = v
                
        # Find explicit Product ID (avoid serial number collision)
        prod_id = None
        for key in ["productid", "prodid", "id", "itemid"]:
            if key in norm_row:
                prod_id = norm_row[key]
                break
                
        # Find Product Name
        prod_name = None
        for key in ["productname", "name", "product", "itemname", "item"]:
            if key in norm_row:
                prod_name = norm_row[key]
                break
                
        # Find New Stock / Qty
        new_stock = None
        for key in ["newstock", "stock", "currentstock", "newqty", "newquantity", "qty", "quantity", "stockcount", "count"]:
            if key in norm_row and norm_row[key] is not None and str(norm_row[key]).strip() != "":
                new_stock = norm_row[key]
                break
                
        if (prod_id or prod_name) and new_stock is not None:
            nstock = parse_csv_int(new_stock, None)
            if nstock is not None:
                product = None
                
                # Compatibility fallback: match by ID if ID column is present and valid
                cleaned_prod_id = clean_csv_val(prod_id)
                if cleaned_prod_id:
                    try:
                        pid = int(float(cleaned_prod_id))
                        product = db.query(Product).filter(
                            Product.id == pid,
                            Product.shopkeeper_id == shopkeeper_id,
                            Product.is_deleted == False
                        ).first()
                    except ValueError:
                        pass
                        
                # Primary modern matching: match by Product Name (robust space/hyphen insensitive)
                cleaned_prod_name = clean_csv_val(prod_name)
                if not product and cleaned_prod_name:
                    p_name_norm = cleaned_prod_name.lower().replace(' ', '').replace('-', '')
                    product = db.query(Product).filter(
                        func.replace(func.replace(func.lower(Product.name), ' ', ''), '-', '') == p_name_norm,
                        Product.shopkeeper_id == shopkeeper_id,
                        Product.is_deleted == False
                    ).first()
                    
                if product:
                    inv = db.query(ShopInventory).filter(
                        ShopInventory.shopkeeper_id == shopkeeper_id,
                        ShopInventory.product_id == product.id
                    ).first()
                    if not inv:
                        inv = ShopInventory(shopkeeper_id=shopkeeper_id, product_id=product.id, stock=nstock)
                        db.add(inv)
                    else:
                        inv.stock += nstock
                    updated_count += 1
                    
    db.commit()
    return {"status": "success", "detail": f"Successfully updated {updated_count} items."}

