import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sys

# Need to append the path so we can import models from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import SessionLocal, Product

def seed():
    db = SessionLocal()
    
    products_data = [
        ("Clothwash 1 liter", 80),
        ("Dishwash 1 liter", 50),
        ("Floorwash 1 liter", 50),
        ("Toilet cleaner 1 liter", 50),
        ("Handwash 1 liter", 50),
        ("Comfort 1 liter", 80),
        ("Clothwash 5 liter", 300),
        ("Dishwash 5 liter", 300),
        ("Floorwash 5 liter", 300),
        ("Toilet cleaner 5 liter", 300),
        ("Handwash 5 liter", 300),
        ("Comfort 5 liter", 300),
        ("Dishwash 500ml", 50),
        ("Floorwash 500ml", 40),
        ("Toilet cleaner 500ml", 40),
        ("Handwash 500ml", 50)
    ]
    
    print("Clearing existing products...")
    db.query(Product).delete()
    
    for name, price in products_data:
        # Generate predictable image filename, e.g. 'clothwash_1_liter.jpg'
        image_filename = name.lower().replace(" ", "_").replace("-", "") + ".jpg"
        
        # Initial stock to 10 for everything
        product = Product(name=name, price=price, stock=10, image_filename=image_filename)
        db.add(product)
        print(f"Added: {name} - Rs{price} (Image: {image_filename})")
        
    db.commit()
    print("Done seeding 16 products.")
    db.close()

if __name__ == "__main__":
    seed()
