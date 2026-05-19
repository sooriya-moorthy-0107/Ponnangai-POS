
import os
import sys

# Append path to import from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import SessionLocal, Product, ShopInventory, User, Base, engine

def migrate():
    # Ensure tables are created (creates shop_inventories)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Get all products
    products = db.query(Product).all()
    # Get all shopkeepers
    shopkeepers = db.query(User).filter(User.role == "Shopkeeper").all()
    
    if not shopkeepers:
        print("No shopkeepers found.")
        return
        
    for shopkeeper in shopkeepers:
        for product in products:
            existing = db.query(ShopInventory).filter(
                ShopInventory.shopkeeper_id == shopkeeper.id,
                ShopInventory.product_id == product.id
            ).first()
            
            if not existing:
                # Seed with 10 for the default 'shopkeeper', 0 for others
                stock = 10 if shopkeeper.username == "shopkeeper" else 0
                new_inv = ShopInventory(shopkeeper_id=shopkeeper.id, product_id=product.id, stock=stock)
                db.add(new_inv)
                
    db.commit()
    print("Migration completed: ShopInventory created and populated.")
    db.close()

if __name__ == "__main__":
    migrate()
