import os
import sys
import io
import csv
import pytest

# Add parent dir to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from main import app
from app.models.database import get_db, engine, Base
from app.models.domain import User, Product, ShopInventory

client = TestClient(app)

def setup_module(module):
    Base.metadata.create_all(bind=engine)

def test_inventory_bulk_upload_stock_logic():
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Create a test shopkeeper user if not existing
        shopkeeper = db.query(User).filter(User.username == "test_shopkeeper_upload").first()
        if not shopkeeper:
            shopkeeper = User(
                username="test_shopkeeper_upload",
                password="fake",
                role="Shopkeeper"
            )
            db.add(shopkeeper)
            db.commit()
            db.refresh(shopkeeper)

        # Create two products for this shopkeeper
        p1 = db.query(Product).filter(Product.name == "Test Item Alpha", Product.shopkeeper_id == shopkeeper.id).first()
        if not p1:
            p1 = Product(name="Test Item Alpha", price=100.0, shopkeeper_id=shopkeeper.id)
            db.add(p1)
            
        p2 = db.query(Product).filter(Product.name == "Test Item Beta", Product.shopkeeper_id == shopkeeper.id).first()
        if not p2:
            p2 = Product(name="Test Item Beta", price=150.0, shopkeeper_id=shopkeeper.id)
            db.add(p2)
            
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        # Set initial stock: Item Alpha = 10, Item Beta = 20
        inv1 = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper.id, ShopInventory.product_id == p1.id).first()
        if not inv1:
            inv1 = ShopInventory(shopkeeper_id=shopkeeper.id, product_id=p1.id, stock=10)
            db.add(inv1)
        else:
            inv1.stock = 10
            
        inv2 = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == shopkeeper.id, ShopInventory.product_id == p2.id).first()
        if not inv2:
            inv2 = ShopInventory(shopkeeper_id=shopkeeper.id, product_id=p2.id, stock=20)
            db.add(inv2)
        else:
            inv2.stock = 20
            
        db.commit()

        # Build CSV matching the standard template format
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["S.No.", "Product Name", "Current Stock", "New Stock"])
        # Product Alpha: current stock 10, new stock 20 (should result in 10 + 20 = 30)
        writer.writerow([1, "Test Item Alpha", 10, 20])
        # Product Beta: current stock 20, new stock BLANK (should remain 20, NOT become 20 + 20 = 40)
        writer.writerow([2, "Test Item Beta", 20, ""])

        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        # Patch get_current_user in inventory route module
        import app.api.routes.inventory as inv_module
        original_get_current_user = inv_module.get_current_user
        inv_module.get_current_user = lambda req, db: shopkeeper

        try:
            response = client.post(
                "/api/inventory/bulk_upload",
                data={"shopkeeper_id": shopkeeper.id},
                files={"file": ("inventory.csv", csv_bytes, "text/csv")}
            )
        finally:
            inv_module.get_current_user = original_get_current_user

        assert response.status_code == 200, response.json()
        assert response.json()["status"] == "success"

        # Refresh inventory from DB
        db.refresh(inv1)
        db.refresh(inv2)

        # Assert Item Alpha stock updated to 10 + 20 = 30
        assert inv1.stock == 30, f"Expected 30, got {inv1.stock}"
        # Assert Item Beta stock remained 20 (not 40!)
        assert inv2.stock == 20, f"Expected 20, got {inv2.stock}"

    finally:
        db.close()
