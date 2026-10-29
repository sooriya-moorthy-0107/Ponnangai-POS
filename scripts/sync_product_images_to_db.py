"""
Script to update all products in the database with their matching photo filenames.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.database import SessionLocal
from app.models.domain import Product
from app.utils.photo_mapper import auto_map_product_photo

def sync_images():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        print(f"Syncing photo filenames for {len(products)} products in database...")
        updated = 0
        for p in products:
            new_image = auto_map_product_photo(p.name)
            if p.image_filename != new_image:
                print(f"  [UPDATE] {p.name}: '{p.image_filename}' -> '{new_image}'")
                p.image_filename = new_image
                updated += 1
            else:
                print(f"  [OK] {p.name}: '{p.image_filename}'")
                
        db.commit()
        print(f"\nDatabase sync complete! Updated {updated} of {len(products)} products.")
    finally:
        db.close()

if __name__ == "__main__":
    sync_images()
