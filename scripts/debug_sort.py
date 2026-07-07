import sys
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add local path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.domain import Base, Product, User, ShopInventory

# Connect to the local SQLite database used for development/testing if needed, or point to production DB
engine = create_engine('sqlite:///./test.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

base_order = [
    "Cloth wash",
    "Comfort",
    "Dish wash",
    "Floor Cleaner",
    "Toilet cleaner",
    "Tiles Cleaner",
    "Glass cleaner",
    "Hand wash",
    "Phenoyl",
    "Phenoyl compound",
    "Peethambari",
    "Odonil zipper",
    "Checked cloth",
    "Odonil cake",
    "Dustbin cover small",
    "Dustbin cover medium",
    "Dustbin cover large",
    "Dustbin cover Extra large",
    "Silver polish",
    "Mini scent",
    "Dish wash soap",
    "Multi cake",
    "Sambrani Box",
    "Agarbatthi",
    "Sink cleaner drainex powder",
    "Mop stick",
    "Mop base",
    "Mat",
    "Toilet brush double side",
    "Napthelene balls pkt",
    "Green Scrubber",
    "Steel Scrubber",
    "Bleaching powder",
    "Ant chalk",
    "Soft broom",
    "Tissue pkt",
    "Box Room Spray",
    "Bathing Soap",
    "Sambrani pcs",
    "Eytex Zipper",
    "Eytex Cake",
    "Soapoil",
    "Multi purpose"
]

def get_product_sort_key(product_name):
    name_lower = product_name.lower().strip()
    
    # 1. Determine base category index
    base_idx = 999
    matched_base = ""
    for i, base in enumerate(base_order):
        if base.lower() in name_lower:
            # We want the longest match (e.g. "Dustbin cover small" vs "Dustbin cover")
            if len(base) > len(matched_base):
                base_idx = i
                matched_base = base.lower()
                
    if base_idx == 999:
        # If completely unknown, push to end, sort alphabetically
        return (999, 999, product_name)
        
    # 2. Determine sub-variant index (Sticker -> WOS -> 5 ltr)
    variant_idx = 1 # default is sticker (or base item)
    if "wos" in name_lower or "water bottle" in name_lower or "1/2 ltr" in name_lower:
        variant_idx = 2
    elif "5 ltr" in name_lower or "5l" in name_lower or "5 l" in name_lower:
        variant_idx = 3
        
    return (base_idx, variant_idx, product_name)

products = db.query(Product).all()
if not products:
    # Let's just create some dummy names to test
    dummy_names = [
        "Floor cleaner WATER BOTTLE", "Cloth wash  5 ltr can", "Comfort STICKER",
        "Cloth wash", "Comfort", "Dish wash 5 ltr can", "Floor Cleaner 5 ltr can",
        "Tiles Cleaner STICKER", "Mop stick", "Agarbatthi", "Toilet Cleaner  WATER BOTTLE"
    ]
    class MockProduct:
        def __init__(self, name):
            self.name = name
    products = [MockProduct(n) for n in dummy_names]

products.sort(key=lambda p: get_product_sort_key(p.name))

for p in products:
    print(f"{get_product_sort_key(p.name)} - {p.name}")


