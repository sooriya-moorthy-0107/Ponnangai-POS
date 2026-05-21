import os
import csv
import io
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, UploadFile, File, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from starlette.middleware.sessions import SessionMiddleware

# --- Configuration & Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ponnangai_pos.db")

# Adjust postgres scheme for SQLAlchemy 1.4+ compatibility if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure database engine based on dialect
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

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
    is_deleted = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    image_filename = Column(String, nullable=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)

    shopkeeper = relationship("User")

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

# Schema upgrade (adding shopkeeper_id and is_deleted columns dynamically if missing)
db_init = SessionLocal()
try:
    if DATABASE_URL.startswith("sqlite:///"):
        db_init.execute(text("ALTER TABLE products ADD COLUMN shopkeeper_id INTEGER"))
    else:
        db_init.execute(text("ALTER TABLE products ADD COLUMN shopkeeper_id INTEGER REFERENCES users(id)"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("ALTER TABLE products ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
    db_init.commit()
except Exception:
    db_init.rollback()

# Ensure all products have is_deleted set to FALSE if it is NULL
try:
    db_init.execute(text("UPDATE products SET is_deleted = FALSE WHERE is_deleted IS NULL"))
    db_init.commit()
except Exception:
    db_init.rollback()

# Upgrade users table to support soft delete/archiving
try:
    db_init.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("UPDATE users SET is_deleted = FALSE WHERE is_deleted IS NULL"))
    db_init.commit()
except Exception:
    db_init.rollback()

# Migration: Assign existing products without shopkeeper_id to the first Shopkeeper
try:
    first_sk = db_init.query(User).filter(User.role == "Shopkeeper").first()
    if first_sk:
        db_init.execute(text(f"UPDATE products SET shopkeeper_id = {first_sk.id} WHERE shopkeeper_id IS NULL"))
        db_init.commit()
except Exception as e:
    db_init.rollback()
    print(f"Startup migration error: {e}")
finally:
    db_init.close()

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
    return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

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
    username_clean = username.strip()
    user = db.query(User).filter(User.username == username_clean, User.is_deleted == False).first()
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
    
    # Only show products that have a stock > 0 in this shopkeeper's inventory
    inventory = db.query(ShopInventory).filter(
        ShopInventory.shopkeeper_id == user.id,
        ShopInventory.stock > 0
    ).all()
    inv_map = {inv.product_id: inv.stock for inv in inventory}
    
    product_ids = list(inv_map.keys())
    if product_ids:
        products = db.query(Product).filter(Product.id.in_(product_ids), Product.is_deleted == False).all()
        for p in products:
            p.stock = inv_map.get(p.id, 0)
    else:
        products = []
        
    return templates.TemplateResponse(request=request, name="shop.html", context={"request": request, "user": user, "products": products})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # Owner, Admin, Manager have access to the dashboard
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    products = db.query(Product).filter(Product.is_deleted == False).all()
    # Filter out soft-deleted users/staff from active views
    users = db.query(User).filter(User.is_deleted == False).all()
    shopkeepers = [u for u in users if u.role == "Shopkeeper"]
    
    # Load archived shopkeepers specifically for historical analytics
    archived_shopkeepers = db.query(User).filter(User.role == "Shopkeeper", User.is_deleted == True).all()
    
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
    
    # Low stock alerts across active shops and active products (ignores soft-deleted stocks)
    low_stock_alerts = db.query(ShopInventory).join(Product).join(User, ShopInventory.shopkeeper_id == User.id).filter(
        ShopInventory.stock < 10,
        Product.is_deleted == False,
        User.is_deleted == False
    ).all()
    
    # Shop performance for active shopkeepers
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
        "archived_shopkeepers": archived_shopkeepers,
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
        
    return templates.TemplateResponse(request=request, name="receipt.html", context={"request": request, "bill": bill, "user": user})

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
            "discount": b.discount,
            "final_amount": b.final_amount,
            "payment_mode": b.payment_mode,
            "timestamp": b.timestamp.strftime('%Y-%m-%d %H:%M'),
            "cashier_name": b.cashier_name
        })
        
    return {"status": "success", "bills": result}

@app.get("/api/bills/{bill_id}")
async def get_bill_details(request: Request, bill_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
    
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return JSONResponse(status_code=404, content={"detail": "Bill not found"})
        
    items = []
    for item in bill.items:
        items.append({
            "product_id": item.product_id,
            "name": item.product.name if item.product else "Deleted Item",
            "quantity": item.quantity,
            "price": item.price_at_sale,
            "total": item.price_at_sale * item.quantity
        })
        
    return {
        "status": "success",
        "bill": {
            "id": bill.id,
            "total_amount": bill.total_amount,
            "discount": bill.discount,
            "final_amount": bill.final_amount,
            "payment_mode": bill.payment_mode,
            "timestamp": bill.timestamp.strftime('%Y-%m-%d %H:%M'),
            "cashier_name": bill.cashier_name,
            "items": items
        }
    }

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
    if not user or user.role not in ["Admin", "Manager", "Owner", "Shopkeeper"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    if user.role == "Shopkeeper" and user.id != shopkeeper_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Shopkeepers can only access their own inventory template.")
    
    # Query only active products scoped to this shopkeeper
    products = db.query(Product).filter(
        Product.shopkeeper_id == shopkeeper_id,
        Product.is_deleted == False
    ).all()
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

@app.post("/api/inventory/bulk_upload")
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
        decoded = content.decode('utf-8')
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Could not decode file. Ensure it is a valid CSV."})
        
    reader = csv.DictReader(io.StringIO(decoded))
    
    updated_count = 0
    for row in reader:
        prod_id = row.get("Product ID") or row.get("product_id")
        prod_name = row.get("Product Name") or row.get("name") or row.get("Product")
        new_stock = row.get("New Stock") or row.get("stock") or row.get("NewStock")
        
        if (prod_id or prod_name) and new_stock and str(new_stock).strip() != "":
            try:
                nstock = int(float(new_stock))
                product = None
                
                # Compatibility fallback: match by ID if ID column is present and has integer value
                if prod_id and str(prod_id).strip() != "":
                    try:
                        pid = int(float(prod_id))
                        product = db.query(Product).filter(
                            Product.id == pid,
                            Product.shopkeeper_id == shopkeeper_id,
                            Product.is_deleted == False
                        ).first()
                    except ValueError:
                        pass
                
                # Primary modern matching: match by Product Name (case-insensitive stripped lookup)
                if not product and prod_name:
                    p_name = str(prod_name).strip().lower()
                    product = db.query(Product).filter(
                        func.lower(func.trim(Product.name)) == p_name,
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
    shopkeeper_id = data.get("shopkeeper_id")
    
    if not name or price is None or not shopkeeper_id:
        return JSONResponse(status_code=400, content={"detail": "Missing name, price, or shopkeeper_id"})
        
    new_product = Product(name=name, price=float(price), shopkeeper_id=int(shopkeeper_id), is_deleted=False)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Initialize stock for the specific shopkeeper
    db.add(ShopInventory(shopkeeper_id=int(shopkeeper_id), product_id=new_product.id, stock=int(stock)))
    db.commit()
    
    return {"status": "success", "detail": "Product added to shop successfully"}

@app.get("/api/products/template")
async def get_products_template(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product Name", "Price", "Initial Stock", "Image Name"])
    writer.writerow(["Soft Broom", "120.00", "20", "Soft Broom Front"])
    writer.writerow(["Hard Broom", "150.00", "20", "Hard broom photo"])
    writer.writerow(["Mop", "200.00", "20", "mop pic"])
    writer.writerow(["Clothwash 1 liter", "80.00", "50", "clothwash"])
    
    headers = {
        "Content-Disposition": "attachment; filename=products_bulk_template.csv"
    }
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

@app.post("/api/products/bulk_upload")
async def bulk_upload_products(request: Request, shopkeeper_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
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
    
    added_count = 0
    updated_count = 0
    
    for row in reader:
        name = row.get("Product Name") or row.get("name") or row.get("Product")
        price_val = row.get("Price") or row.get("price") or row.get("Rate")
        stock_val = row.get("Initial Stock") or row.get("stock") or row.get("initial_stock") or row.get("Stock")
        image_val = row.get("Image Name") or row.get("image") or row.get("Image Filename")
        
        if name and price_val:
            try:
                p_name = str(name).strip()
                p_price = float(price_val)
                p_stock = int(float(stock_val)) if (stock_val and str(stock_val).strip() != "") else 0
                
                # Check if product already exists for this shopkeeper (active or soft-deleted, case-insensitive)
                existing = db.query(Product).filter(
                    func.lower(func.trim(Product.name)) == p_name.lower(),
                    Product.shopkeeper_id == shopkeeper_id
                ).first()
                
                if existing:
                    # Update existing product (reactivate if soft-deleted)
                    existing.price = p_price
                    existing.is_deleted = False
                    if image_val and str(image_val).strip() != "":
                        raw_img = str(image_val).strip()
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
                        inv.stock = p_stock
                    db.commit()
                    updated_count += 1
                else:
                    # Create new shopkeeper-specific product
                    if image_val and str(image_val).strip() != "":
                        raw_img = str(image_val).strip()
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
                        is_deleted=False
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

@app.post("/api/products/delete")
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
        
    existing_user = db.query(User).filter(User.username == username, User.is_deleted == False).first()
    if existing_user:
        return JSONResponse(status_code=400, content={"detail": "Username already exists"})
        
    new_user = User(username=username, password=password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Every new shop starts from zero and doesn't auto-create zero-stock inventory records.
        
    return {"status": "success", "detail": f"{role} '{username}' created successfully"}

@app.post("/api/users/edit")
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

@app.post("/api/users/delete")
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

@app.post("/api/products/{product_id}/image")
async def upload_product_image(request: Request, product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
        
    if not file.filename:
        return JSONResponse(status_code=400, content={"detail": "No file uploaded"})
        
    # Generate clean filename based on product ID
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        ext = ".jpg"
    new_filename = f"product_{product_id}{ext}"
    file_path = os.path.join("photos", new_filename)
    
    # Save the file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Update DB
    product.image_filename = new_filename
    db.commit()
    
    return {"status": "success", "detail": "Photo updated successfully!", "image_filename": new_filename}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
