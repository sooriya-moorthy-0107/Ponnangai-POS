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

@router.post("/api/products/{product_id}/edit")
async def edit_product_info(request: Request, product_id: int, name: str = Form(...), price: float = Form(None), rate_qty: float = Form(None), stock: int = Form(None), shopkeeper_id: int = Form(None), db: Session = Depends(get_db)):
    
    form_data = await request.form()
    file = form_data.get("file")
    
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
        
    product.name = name.strip()
    if price is not None:
        product.price = price
    if rate_qty is not None:
        product.rate_qty = rate_qty
    
    if stock is not None and shopkeeper_id is not None:
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.product_id == product_id,
            ShopInventory.shopkeeper_id == shopkeeper_id
        ).first()
        if shop_inv:
            shop_inv.stock = stock
        else:
            new_inv = ShopInventory(shopkeeper_id=shopkeeper_id, product_id=product_id, stock=stock)
            db.add(new_inv)
    
    if file and hasattr(file, "filename") and file.filename:
        if not file.content_type or not file.content_type.startswith("image/"):
            return JSONResponse(status_code=400, content={"detail": "Invalid file type. Only image files are allowed."})
            
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".jpg"
        new_filename = f"product_{product_id}_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join("photos", new_filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        product.image_filename = new_filename
        
    db.commit()
    
    debug_msg = f"File present: {file is not None}"
    if file:
        debug_msg += f", filename: {getattr(file, 'filename', None)}"
        
    return {"status": "success", "detail": f"Product updated successfully! Debug: {debug_msg}"}

@router.post("/api/products/add")
async def add_product(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock", 0)
    shopkeeper_id = data.get("shopkeeper_id")
    product_type = data.get("product_type", "solid")
    unit = data.get("unit", "Pcs")
    
    if not name or price is None or not shopkeeper_id:
        return JSONResponse(status_code=400, content={"detail": "Missing name, price, or shopkeeper_id"})
        
    new_product = Product(
        name=name,
        price=float(price),
        shopkeeper_id=int(shopkeeper_id),
        is_deleted=False,
        product_type=product_type,
        unit=unit
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Initialize stock for the specific shopkeeper
    db.add(ShopInventory(shopkeeper_id=int(shopkeeper_id), product_id=new_product.id, stock=int(stock)))
    db.commit()
    
    return {"status": "success", "detail": "Product added to shop successfully"}

@router.get("/api/products/template")
async def get_products_template(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product Name", "Price", "Initial Stock", "Product Type", "Unit", "Image Name"])
    writer.writerow(["Soft Broom", "120.00", "20", "solid", "Pcs", "Soft Broom Front"])
    writer.writerow(["Hard Broom", "150.00", "20", "solid", "Pcs", "Hard broom photo"])
    writer.writerow(["Mop", "200.00", "20", "solid", "Pcs", "mop pic"])
    writer.writerow(["Clothwash", "80.00", "0", "liquid", "Liters", "clothwash"])
    
    headers = {
        "Content-Disposition": "attachment; filename=products_bulk_template.csv"
    }
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

@router.post("/api/products/bulk_upload")
async def bulk_upload_products(request: Request, shopkeeper_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
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
    
    added_count = 0
    updated_count = 0
    
    for row in reader:
        # Standardize keys by lowercasing and stripping special chars
        norm_row = {}
        for k, v in row.items():
            if k is not None:
                norm_key = str(k).strip().lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
                norm_row[norm_key] = v
                
        name = None
        for key in ["productname", "name", "product", "itemname", "item"]:
            if key in norm_row:
                name = norm_row[key]
                break

        price_val = None
        for key in ["price", "rate", "cost", "mrp", "unitprice", "amount"]:
            if key in norm_row:
                price_val = norm_row[key]
                break

        stock_val = None
        for key in ["initialstock", "stock", "newstock", "qty", "quantity", "initialqty", "currentstock", "count"]:
            if key in norm_row:
                stock_val = norm_row[key]
                break

        product_type_val = None
        for key in ["producttype", "type", "category"]:
            if key in norm_row:
                product_type_val = norm_row[key]
                break

        unit_val = None
        for key in ["unit", "measure"]:
            if key in norm_row:
                unit_val = norm_row[key]
                break

        image_val = None
        for key in ["imagename", "image", "imagefilename", "img", "photo", "pic"]:
            if key in norm_row:
                image_val = norm_row[key]
                break
                
        cleaned_name = clean_csv_val(name)
        cleaned_price = clean_csv_val(price_val)
        cleaned_product_type = clean_csv_val(product_type_val)
        cleaned_unit = clean_csv_val(unit_val)
        
        if cleaned_name and cleaned_price:
            try:
                p_name = cleaned_name
                p_price = float(cleaned_price)
                
                # Check for explicit stock
                p_stock = 0
                if stock_val is not None:
                    p_stock = parse_csv_int(stock_val, 0)
                    
                p_type = "solid"
                if cleaned_product_type and cleaned_product_type.lower() == "liquid":
                    p_type = "liquid"
                    
                p_unit = "Pcs"
                if cleaned_unit:
                    p_unit = cleaned_unit
                
                # Check if product already exists for this shopkeeper (active or soft-deleted, robust space & hyphen insensitive)
                p_name_norm = p_name.lower().replace(' ', '').replace('-', '')
                existing = db.query(Product).filter(
                    func.replace(func.replace(func.lower(Product.name), ' ', ''), '-', '') == p_name_norm,
                    Product.shopkeeper_id == shopkeeper_id
                ).first()
                
                if existing:
                    # Update existing product (reactivate if soft-deleted)
                    existing.price = p_price
                    existing.is_deleted = False
                    existing.product_type = p_type
                    existing.unit = p_unit
                    cleaned_image = clean_csv_val(image_val)
                    if cleaned_image:
                        raw_img = cleaned_image
                        image_filename = raw_img.lower().replace(" ", "_").replace("-", "")
                        if not image_filename.endswith(".jpg"):
                            image_filename += ".jpg"
                        existing.image_filename = image_filename
                    db.commit()
                    
                    # Update or create ShopInventory record
                    inv = db.query(ShopInventory).filter(
                        ShopInventory.shopkeeper_id == shopkeeper_id,
                        ShopInventory.product_id == existing.id
                    ).first()
                    if not inv:
                        inv = ShopInventory(shopkeeper_id=shopkeeper_id, product_id=existing.id, stock=p_stock)
                        db.add(inv)
                    else:
                        inv.stock += p_stock
                    db.commit()
                    updated_count += 1
                else:
                    # Create new shopkeeper-specific product
                    cleaned_image = clean_csv_val(image_val)
                    if cleaned_image:
                        raw_img = cleaned_image
                        image_filename = raw_img.lower().replace(" ", "_").replace("-", "")
                        if not image_filename.endswith(".jpg"):
                            image_filename += ".jpg"
                    else:
                        image_filename = p_name.lower().replace(" ", "_").replace("-", "") + ".jpg"
                    
                    new_product = Product(
                        name=p_name,
                        price=p_price,
                        image_filename=image_filename,
                        shopkeeper_id=shopkeeper_id,
                        is_deleted=False,
                        product_type=p_type,
                        unit=p_unit
                    )
                    db.add(new_product)
                    db.commit()
                    db.refresh(new_product)
                    
                    # Add stock to shop inventory
                    db.add(ShopInventory(shopkeeper_id=shopkeeper_id, product_id=new_product.id, stock=p_stock))
                    db.commit()
                    added_count += 1
            except (ValueError, TypeError):
                continue
                
    return {"status": "success", "detail": f"Successfully processed CSV: added {added_count} products and updated {updated_count} products."}

@router.post("/api/products/delete")
async def delete_product(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product_id = data.get("id")
    if product_id is None:
        return JSONResponse(status_code=400, content={"detail": "Missing product ID"})
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid product ID format"})
        
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
        
    # Soft delete: set is_deleted = True and set stock = 0
    product.is_deleted = True
    db.query(ShopInventory).filter(ShopInventory.product_id == product_id).update({ShopInventory.stock: 0})
    db.commit()
    
    return {"status": "success", "detail": f"Product '{product.name}' deleted successfully"}

@router.post("/api/products/{product_id}/image")
async def upload_product_image(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    
    form_data = await request.form()
    file = form_data.get("file")
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
        
    if not file.filename:
        return JSONResponse(status_code=400, content={"detail": "No file uploaded"})
        
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"detail": "Invalid file type. Only image files are allowed."})
        
    # Generate clean filename based on product ID
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        ext = ".jpg"
    new_filename = f"product_{product_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join("photos", new_filename)
    
    # Save the file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Update DB
    # Update DB
    product.image_filename = new_filename
    db.commit()
    
    debug_msg = f"File present: {file is not None}"
    if file:
        debug_msg += f", filename: {getattr(file, 'filename', None)}"
        
    return {"status": "success", "detail": f"Photo updated successfully! Debug: {debug_msg}", "image_filename": new_filename}

