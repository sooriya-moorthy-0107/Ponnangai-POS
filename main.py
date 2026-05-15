import os
import csv
import io
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, UploadFile, File, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from starlette.middleware.sessions import SessionMiddleware

# --- Configuration & Setup ---
DATABASE_URL = "sqlite:///./ponnangai_pos.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Ponnangai POS")
# Using Starlette's SessionMiddleware for simple cookie-based sessions
app.add_middleware(SessionMiddleware, secret_key="ponnangai-super-secret-key")

# Ensure directories exist according to structure
os.makedirs("templates", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("photos", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/photos", StaticFiles(directory="photos"), name="photos")
templates = Jinja2Templates(directory="templates")

# --- Database Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False) # Admin, Owner, Manager, Shopkeeper

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    image_filename = Column(String, nullable=True)

class ShopInventory(Base):
    __tablename__ = "shop_inventories"
    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    stock = Column(Integer, default=0)

    shopkeeper = relationship("User")
    product = relationship("Product")

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False)
    payment_mode = Column(String, default="Cash") # Cash/UPI
    timestamp = Column(DateTime, default=datetime.utcnow)
    cashier_id = Column(Integer, ForeignKey("users.id"))
    cashier_name = Column(String, nullable=True)

    cashier = relationship("User")
    items = relationship("BillItem", back_populates="bill")

class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_at_sale = Column(Float, nullable=False)

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")

# Create tables
Base.metadata.create_all(bind=engine)

# --- Dependencies ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

# --- Initial Seed Data ---
def seed_db():
    db = SessionLocal()
    if db.query(User).count() == 0:
        # Create initial users
        admin = User(username="admin", password="admin123", role="Admin")
        manager = User(username="manager", password="manager123", role="Manager")
        shopkeeper = User(username="shopkeeper", password="shopkeeper123", role="Shopkeeper")
        owner = User(username="owner", password="owner123", role="Owner")
        db.add_all([admin, manager, shopkeeper, owner])
        db.commit()
    else:
        owner = db.query(User).filter(User.role == "Owner").first()
        if not owner:
            owner = User(username="owner", password="owner123", role="Owner")
            db.add(owner)
            db.commit()
    db.close()

seed_db()

# --- Web Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if user.role == "Shopkeeper":
        return RedirectResponse(url="/shop", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@app.post("/login")
async def do_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid username or password"})
    
    request.session["user_id"] = user.id
    
    if user.role == "Shopkeeper":
        return RedirectResponse(url="/shop", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/shop", response_class=HTMLResponse)
async def shop_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    inventory = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == user.id).all()
    inv_map = {inv.product_id: inv.stock for inv in inventory}
    products = db.query(Product).all()
    for p in products:
        p.stock = inv_map.get(p.id, 0)
    return templates.TemplateResponse(request=request, name="shop.html", context={"request": request, "user": user, "products": products})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # Owner, Admin, Manager have access to the dashboard
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    products = db.query(Product).all()
    users = db.query(User).all()
    shopkeepers = [u for u in users if u.role == "Shopkeeper"]
    
    # Inventory mapping: shop_inventory[shopkeeper_id][product_id] = stock
    all_inventory = db.query(ShopInventory).all()
    shop_inventory = {}
    for inv in all_inventory:
        if inv.shopkeeper_id not in shop_inventory:
            shop_inventory[inv.shopkeeper_id] = {}
        shop_inventory[inv.shopkeeper_id][inv.product_id] = inv.stock
        
    # Dashboard metrics
    total_revenue = db.query(func.sum(Bill.final_amount)).scalar() or 0.0
    total_sales = db.query(Bill).count()
    
    # Low stock alerts across all shops
    low_stock_alerts = db.query(ShopInventory).filter(ShopInventory.stock < 10).all()
    
    # Shop performance
    shop_performance = []
    for sk in shopkeepers:
        sales = db.query(Bill).filter(Bill.cashier_id == sk.id).count()
        rev = db.query(func.sum(Bill.final_amount)).filter(Bill.cashier_id == sk.id).scalar() or 0.0
        shop_performance.append({
            "shopkeeper": sk,
            "sales": sales,
            "revenue": rev
        })
    
    return templates.TemplateResponse(request=request, name="admin.html", context={
        "request": request,
        "user": user,
        "products": products,
        "users": users,
        "shopkeepers": shopkeepers,
        "shop_inventory": shop_inventory,
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "low_stock_alerts": low_stock_alerts,
        "shop_performance": shop_performance
    })

@app.get("/receipt/{bill_id}", response_class=HTMLResponse)
async def receipt_page(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    return templates.TemplateResponse(request=request, name="receipt.html", context={"request": request, "bill": bill})

# --- API Routes ---

@app.get("/api/bills/history")
async def get_bill_history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    query = db.query(Bill)
    if user.role == "Shopkeeper":
        query = query.filter(Bill.cashier_id == user.id)
        
    # Get last 20 bills
    bills = query.order_by(Bill.timestamp.desc()).limit(20).all()
    
    result = []
    for b in bills:
        result.append({
            "id": b.id,
            "total_amount": b.total_amount,
            "final_amount": b.final_amount,
            "payment_mode": b.payment_mode,
            "timestamp": b.timestamp.strftime('%Y-%m-%d %H:%M')
        })
        
    return {"status": "success", "bills": result}

@app.post("/api/bills")
async def create_bill(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    # Expected payload: {"items": [{"id": 1, "qty": 2}], "discount": 10.0, "payment_mode": "Cash"}
    total_amount = 0.0
    bill_items = []
    
    for item in data.get("items", []):
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            continue
            
        # Deduct stock
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == user.id, 
            ShopInventory.product_id == product.id
        ).first()
        if shop_inv:
            shop_inv.stock -= item["qty"]
            if shop_inv.stock < 0:
                 shop_inv.stock = 0
             
        line_total = product.price * item["qty"]
        total_amount += line_total
        
        b_item = BillItem(
            product_id=product.id,
            quantity=item["qty"],
            price_at_sale=product.price
        )
        bill_items.append(b_item)
        
    discount = float(data.get("discount", 0.0))
    final_amount = max(0, total_amount - discount)
    
    new_bill = Bill(
        total_amount=total_amount,
        discount=discount,
        final_amount=final_amount,
        payment_mode=data.get("payment_mode", "Cash"),
        cashier_id=user.id,
        cashier_name=user.username
    )
    
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    
    for b_item in bill_items:
        b_item.bill_id = new_bill.id
        db.add(b_item)
        
    db.commit()
    
    return {"status": "success", "bill_id": new_bill.id}

@app.post("/api/bills/{bill_id}/revert")
async def revert_bill(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Shopkeeper", "Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return JSONResponse(status_code=404, content={"detail": "Bill not found"})
        
    items_data = []
    # Revert stock and prepare cart data
    for item in bill.items:
        # Restore stock in shop inventory
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == bill.cashier_id,
            ShopInventory.product_id == item.product_id
        ).first()
        if shop_inv:
            shop_inv.stock += item.quantity
            
        items_data.append({
            "id": item.product.id,
            "name": item.product.name,
            "price": item.price_at_sale,
            "qty": item.quantity
        })
        
    discount = bill.discount
    payment_mode = bill.payment_mode
    
    # Delete bill items and bill
    db.query(BillItem).filter(BillItem.bill_id == bill.id).delete()
    db.delete(bill)
    db.commit()
    
    return {
        "status": "success", 
        "items": items_data,
        "discount": discount,
        "payment_mode": payment_mode
    }

@app.post("/api/users/update_password")
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
        
    target_user.password = new_password
    db.commit()
    return {"status": "success", "detail": f"Password updated for {target_user.username}"}

@app.post("/api/inventory/update")
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

@app.get("/api/inventory/template/{shopkeeper_id}")
async def get_inventory_template(request: Request, shopkeeper_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    shop_invs = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product ID", "Product Name", "Current Stock", "New Stock"])
    
    for inv in shop_invs:
        writer.writerow([inv.product_id, inv.product.name, inv.stock, ""])
        
    headers = {
        "Content-Disposition": f"attachment; filename=shop_{shopkeeper_id}_inventory_template.csv"
    }
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

@app.post("/api/inventory/bulk_upload")
async def bulk_upload_inventory(request: Request, shopkeeper_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    if not file.filename.endswith('.csv'):
        return JSONResponse(status_code=400, content={"detail": "File must be a CSV"})
        
    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Could not decode file. Ensure it is a valid CSV."})
        
    reader = csv.DictReader(io.StringIO(decoded))
    
    updated_count = 0
    for row in reader:
        prod_id = row.get("Product ID")
        new_stock = row.get("New Stock")
        if prod_id and new_stock and str(new_stock).strip() != "":
            try:
                pid = int(prod_id)
                nstock = int(new_stock)
                inv = db.query(ShopInventory).filter(
                    ShopInventory.shopkeeper_id == shopkeeper_id,
                    ShopInventory.product_id == pid
                ).first()
                if inv:
                    inv.stock = nstock
                    updated_count += 1
            except ValueError:
                continue
                
    db.commit()
    return {"status": "success", "detail": f"Successfully updated {updated_count} items."}

@app.post("/api/system/reset")
async def reset_system(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # ONLY Admin
    if not user or user.role != "Admin":
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin can reset the system."})
        
    # Delete all bills and bill items
    db.query(BillItem).delete()
    db.query(Bill).delete()
    
    # Reset all inventory to 0
    db.query(ShopInventory).update({ShopInventory.stock: 0})
    
    db.commit()
    return {"status": "success", "detail": "System successfully reset to zero."}

@app.post("/api/products/add")
async def add_product(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock", 0)
    
    if not name or price is None:
        return JSONResponse(status_code=400, content={"detail": "Missing name or price"})
        
    new_product = Product(name=name, price=float(price))
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Initialize stock for all shopkeepers
    shopkeepers = db.query(User).filter(User.role == "Shopkeeper").all()
    for sk in shopkeepers:
        db.add(ShopInventory(shopkeeper_id=sk.id, product_id=new_product.id, stock=int(stock)))
    db.commit()
    
    return {"status": "success", "detail": "Product added successfully"}

@app.post("/api/products/delete")
async def delete_product(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product_id = data.get("id")
    if product_id is None:
        return JSONResponse(status_code=400, content={"detail": "Missing product ID"})
        
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
        
    # Delete associated shop inventory records first
    db.query(ShopInventory).filter(ShopInventory.product_id == product_id).delete()
    
    # Delete the product
    db.delete(product)
    db.commit()
    
    return {"status": "success", "detail": f"Product '{product.name}' deleted successfully"}

@app.post("/api/users/add")
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
        
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return JSONResponse(status_code=400, content={"detail": "Username already exists"})
        
    new_user = User(username=username, password=password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    if role == "Shopkeeper":
        products = db.query(Product).all()
        for p in products:
            db.add(ShopInventory(shopkeeper_id=new_user.id, product_id=p.id, stock=0))
        db.commit()
        
    return {"status": "success", "detail": f"{role} '{username}' created successfully"}

@app.post("/api/users/edit")
async def edit_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_id = data.get("user_id")
    new_username = data.get("username")
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

@app.post("/api/users/delete")
async def delete_user(request: Request, data: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin/Owner can delete."})
        
    target_id = data.get("user_id")
    target_user = db.query(User).filter(User.id == target_id).first()
    if not target_user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
        
    if target_user.id == user.id:
        return JSONResponse(status_code=400, content={"detail": "Cannot delete yourself"})
        
    # Remove ShopInventory
    db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == target_id).delete()
    
    # Detach Bills to keep historical data intact
    db.query(Bill).filter(Bill.cashier_id == target_id).update({"cashier_id": None})
    
    db.delete(target_user)
    db.commit()
    return {"status": "success", "detail": "User deleted"}

@app.get("/api/analytics/shop/{shop_id}")
async def get_shop_analytics(request: Request, shop_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    target_shop = db.query(User).filter(User.id == shop_id).first()
    if not target_shop:
        return JSONResponse(status_code=404, content={"detail": "Shop not found"})
        
    bills = db.query(Bill).filter(Bill.cashier_id == shop_id).all()
    total_sales = len(bills)
    total_revenue = sum(b.final_amount for b in bills)
    
    items_query = db.query(
        Product.name,
        func.sum(BillItem.quantity).label("total_qty"),
        func.sum(BillItem.quantity * BillItem.price_at_sale).label("total_revenue")
    ).join(BillItem, Product.id == BillItem.product_id)\
     .join(Bill, Bill.id == BillItem.bill_id)\
     .filter(Bill.cashier_id == shop_id)\
     .group_by(Product.name).all()
     
    breakdown = [{"product_name": row[0], "qty": row[1], "revenue": row[2]} for row in items_query]
    
    return {
        "status": "success",
        "shop_name": target_shop.username,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "breakdown": breakdown
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
