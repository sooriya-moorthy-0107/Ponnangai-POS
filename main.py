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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pos_user:pos_password@localhost:5432/ponnangai_pos")

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
    role = Column(String, nullable=False) # Admin, Owner, Manager, Shopkeeper, Factory
    is_deleted = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    image_filename = Column(String, nullable=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    product_type = Column(String, default="solid") # "solid" or "liquid"
    unit = Column(String, default="Pcs") # "Pcs", "Liters", etc.

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
    timestamp = Column(DateTime, default=datetime.now)
    cashier_id = Column(Integer, ForeignKey("users.id"))
    cashier_name = Column(String, nullable=True)
    is_cancelled = Column(Boolean, default=False)

    cashier = relationship("User")
    items = relationship("BillItem", back_populates="bill")

class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False) # Changed from Integer to Float for loose quantity sales
    price_at_sale = Column(Float, nullable=False)
    packaging_type = Column(String, default="loose") # loose, bottle
    bottle_type = Column(String, nullable=True) # Type 1, Type 2, Type 3
    bottle_count = Column(Integer, default=0)

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")



# Create tables
Base.metadata.create_all(bind=engine)

# Schema upgrade (adding shopkeeper_id and is_deleted columns dynamically if missing)
db_init = SessionLocal()

try:
    db_init.execute(text("DROP TABLE IF EXISTS factory_session_balances CASCADE"))
    db_init.commit()
except Exception:
    db_init.rollback()
    
try:
    db_init.execute(text("DROP TABLE IF EXISTS factory_sessions CASCADE"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("DROP TABLE IF EXISTS factory_session_balances"))
    db_init.commit()
except Exception:
    db_init.rollback()
    
try:
    db_init.execute(text("DROP TABLE IF EXISTS factory_sessions"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
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

# Upgrade bills table to support is_cancelled
try:
    db_init.execute(text("ALTER TABLE bills ADD COLUMN is_cancelled BOOLEAN DEFAULT FALSE"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("UPDATE bills SET is_cancelled = FALSE WHERE is_cancelled IS NULL"))
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

# Migration: Add product_type and unit columns to products
try:
    db_init.execute(text("ALTER TABLE products ADD COLUMN product_type VARCHAR DEFAULT 'solid'"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR DEFAULT 'Pcs'"))
    db_init.commit()
except Exception:
    db_init.rollback()

try:
    db_init.execute(text("UPDATE products SET product_type = 'solid' WHERE product_type IS NULL"))
    db_init.execute(text("UPDATE products SET unit = 'Pcs' WHERE unit IS NULL"))
    db_init.commit()
except Exception:
    db_init.rollback()

# Migration: Convert bill_items.quantity to float
try:
    if DATABASE_URL.startswith("sqlite:///"):
        pass
    else:
        db_init.execute(text("ALTER TABLE bill_items ALTER COLUMN quantity TYPE DOUBLE PRECISION"))
    db_init.commit()
except Exception:
    db_init.rollback()
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
        owner = User(username="owner", password="owner123", role="Owner")
        db.add_all([admin, manager, owner])
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
    elif user.role == "Factory":
        return RedirectResponse(url="/factory", status_code=status.HTTP_302_FOUND)
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
    elif user.role == "Factory":
        return RedirectResponse(url="/factory", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/shop", response_class=HTMLResponse)
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

    # Fetch active products for targeted shopkeeper (even if out of stock)
    products = db.query(Product).filter(
        Product.shopkeeper_id == target_shopkeeper_id,
        Product.is_deleted == False
    ).all()
    
    shop_invs = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == target_shopkeeper_id).all()
    inv_map = {inv.product_id: inv.stock for inv in shop_invs}
    
    for p in products:
        p.stock = inv_map.get(p.id, 0)
        
    target_sk = db.query(User).filter(User.id == target_shopkeeper_id).first()
    target_sk_name = target_sk.username if target_sk else "Unknown Shop"
        
    return templates.TemplateResponse(request=request, name="shop.html", context={
        "request": request,
        "user": user,
        "products": products,
        "shopkeepers": shopkeepers,
        "target_shopkeeper_id": target_shopkeeper_id,
        "target_sk_name": target_sk_name
    })

# --- Factory Cashier & Sessions Routes ---

@app.get("/factory", response_class=HTMLResponse)
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
    products = db.query(Product).filter(
        Product.shopkeeper_id == target_cashier_id,
        Product.is_deleted == False
    ).all()
    
    liquid_products = []
    solid_products = []
    for p in products:
        if p.product_type == "liquid":
            liquid_products.append(p)
        else:
            solid_products.append(p)
            
    target_cashier = db.query(User).filter(User.id == target_cashier_id).first()
    cashier_name = target_cashier.username if target_cashier else "Factory"
    
    return templates.TemplateResponse(request=request, name="factory_pos.html", context={
        "request": request,
        "user": user,
        "liquid_products": liquid_products,
        "solid_products": solid_products,
        "target_shopkeeper_id": target_cashier_id,
        "target_cashier_id": target_cashier_id,
        "cashier_name": cashier_name
    })



@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # Owner, Admin, Manager have access to the dashboard
    if not user or user.role not in ["Admin", "Owner", "Manager"]:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    products = db.query(Product).filter(Product.is_deleted == False).all()
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
        
    # Dashboard metrics
    total_revenue = db.query(func.sum(Bill.final_amount)).filter(Bill.is_cancelled == False).scalar() or 0.0
    total_sales = db.query(Bill).filter(Bill.is_cancelled == False).count()
    
    # Low stock alerts across active shops and active products (ignores soft-deleted stocks)
    low_stock_alerts = db.query(ShopInventory).join(Product).join(User, ShopInventory.shopkeeper_id == User.id).filter(
        ShopInventory.stock < 10,
        Product.is_deleted == False,
        User.is_deleted == False
    ).all()
    
    # Shop performance for active shopkeepers
    shop_performance = []
    for sk in shopkeepers:
        sales = db.query(Bill).filter(Bill.cashier_id == sk.id, Bill.is_cancelled == False).count()
        rev = db.query(func.sum(Bill.final_amount)).filter(Bill.cashier_id == sk.id, Bill.is_cancelled == False).scalar() or 0.0
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
        
    bill_number = db.query(Bill).filter(
        Bill.cashier_id == bill.cashier_id,
        Bill.id <= bill.id
    ).count()
        
    return templates.TemplateResponse(request=request, name="receipt.html", context={"request": request, "bill": bill, "bill_number": bill_number, "user": user})

# --- API Routes ---

@app.get("/api/bills/history")
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
        result.append({
            "id": b.id,
            "bill_number": bill_number,
            "total_amount": b.total_amount,
            "discount": b.discount,
            "final_amount": b.final_amount,
            "payment_mode": b.payment_mode,
            "timestamp": b.timestamp.strftime('%Y-%m-%d %H:%M'),
            "cashier_name": b.cashier_name,
            "is_cancelled": b.is_cancelled
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
            "total": item.price_at_sale * item.quantity
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

@app.post("/api/bills")
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
    final_amount = max(0.0, total_amount - discount)
    
    cashier_name = sk_user.username
    if user.id != sk_user.id:
        cashier_name = f"{sk_user.username} ({user.username})"
    
    new_bill = Bill(
        total_amount=total_amount,
        discount=discount,
        final_amount=final_amount,
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


from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/api/reports/daily")
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
            if item.packaging_type == "bottle" and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.quantity)
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
                    "total_revenue": 0.0,
                    "bottle_count": 0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)
            if pkg_type == "bottle":
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
    
    return {"status": "success", "data": results, "shop_role": shop_role, "bottle_counts": bottle_counts, "revenue_breakdown": revenue_breakdown}

@app.get("/api/reports/daily/export")
async def export_daily_report(request: Request, shopkeeper_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["Admin", "Manager", "Owner"]:
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
            if item.packaging_type == "bottle" and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.quantity)
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
                    "total_revenue": 0.0,
                    "bottle_count": 0
                }
            
            report_data[key]["total_quantity"] += item.quantity
            report_data[key]["total_revenue"] += (item.quantity * item.price_at_sale)
            if pkg_type == "bottle":
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
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Sales_Report_{shop_name}_{t_start.strftime("%Y-%m-%d")}_to_{t_end.strftime("%Y-%m-%d")}.csv"'
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

@app.post("/api/bills/{bill_id}/revert")
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

@app.get("/api/inventory/data/{shopkeeper_id}")
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
    
    shop_invs = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper_id).all()
    inv_map = {inv.product_id: inv.stock for inv in shop_invs}
    
    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": inv_map.get(p.id, 0),
            "image_filename": p.image_filename
        })
        
    return {"status": "success", "products": data}

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

def clean_csv_val(val):
    if val is None:
        return ""
    s = str(val).strip()
    if len(s) >= 2:
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
    return s

def parse_csv_int(val, default=None):
    cleaned = clean_csv_val(val)
    if not cleaned:
        return default
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

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

@app.post("/api/system/reset")
async def reset_system(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # ONLY Admin
    if not user or user.role != "Admin":
        return JSONResponse(status_code=403, content={"detail": "Unauthorized. Only Admin can reset the system."})
        
    # Delete all operational data (preserving users) and reset auto-increment IDs
    dialect = engine.dialect.name
    if dialect == 'sqlite':
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(ShopInventory).delete()
        db.query(Product).delete()
        db.query(User).filter(User.is_deleted == True).delete()
        try:
            db.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('bill_items', 'bills', 'shop_inventories', 'products')"))
        except Exception:
            pass
    elif dialect in ['postgresql', 'postgres']:
        db.execute(text("TRUNCATE TABLE bill_items, bills, shop_inventories, products RESTART IDENTITY CASCADE"))
        db.query(User).filter(User.is_deleted == True).delete()
    else:
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(ShopInventory).delete()
        db.query(Product).delete()
        db.query(User).filter(User.is_deleted == True).delete()
    
    # Also clean up any uploaded product image files starting with "product_" to free disk space
    try:
        if os.path.exists("photos"):
            for filename in os.listdir("photos"):
                if filename.startswith("product_"):
                    os.remove(os.path.join("photos", filename))
    except Exception:
        pass
        
    db.commit()
    return {"status": "success", "detail": "System, products, and sales successfully reset."}

@app.post("/api/products/add")
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

@app.get("/api/products/template")
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

@app.post("/api/products/bulk_upload")
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
