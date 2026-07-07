import os

content = open("main.py", encoding="utf-8").read()

sort_function_str = """
def get_product_sort_key(product_name):
    name_lower = product_name.lower().strip()
    base_order = [
        "Cloth wash", "Comfort", "Dish wash", "Floor Cleaner", "Toilet cleaner",
        "Tiles Cleaner", "Glass cleaner", "Hand wash", "Phenoyl", "Phenoyl compound",
        "Peethambari", "Odonil zipper", "Checked cloth", "Odonil cake",
        "Dustbin cover small", "Dustbin cover medium", "Dustbin cover large",
        "Dustbin cover Extra large", "Silver polish", "Mini scent", "Dish wash soap",
        "Multi cake", "Sambrani Box", "Agarbatthi", "Sink cleaner drainex powder",
        "Mop stick", "Mop base", "Mat", "Toilet brush double side", "Napthelene balls pkt",
        "Green Scrubber", "Steel Scrubber", "Bleaching powder", "Ant chalk",
        "Soft broom", "Tissue pkt", "Box Room Spray", "Bathing Soap", "Sambrani pcs",
        "Eytex Zipper", "Eytex Cake", "Soapoil", "Multi purpose"
    ]
    base_idx = 999
    matched_base = ""
    for i, base in enumerate(base_order):
        if base.lower() in name_lower:
            if len(base) > len(matched_base):
                base_idx = i
                matched_base = base.lower()
                
    if base_idx == 999:
        return (999, 999, product_name)
        
    variant_idx = 1
    if "wos" in name_lower or "water bottle" in name_lower or "1/2 ltr" in name_lower:
        variant_idx = 2
    elif "5 ltr" in name_lower or "5l" in name_lower or "5 l" in name_lower:
        variant_idx = 3
        
    return (base_idx, variant_idx, product_name)
"""

if "def get_product_sort_key" not in content:
    # Insert right before Base = declarative_base()
    content = content.replace("Base = declarative_base()", sort_function_str + "\nBase = declarative_base()")

# Now, we need to sort the products list in 3 places.
# 1. factory_pos_page
str1 = """    products = db.query(Product).filter(
        Product.shopkeeper_id == target_cashier_id,
        Product.is_deleted == False
    ).all()"""
if str1 in content:
    content = content.replace(str1, str1 + "\n    products.sort(key=lambda p: get_product_sort_key(p.name))")
    
# 2. shop_page
str2 = """    products = db.query(Product).filter(
        Product.shopkeeper_id == target_shopkeeper_id,
        Product.is_deleted == False
    ).all()"""
if str2 in content:
    content = content.replace(str2, str2 + "\n    products.sort(key=lambda p: get_product_sort_key(p.name))")

# 3. get_shopkeeper_inventory_data
str3 = """    products = db.query(Product).filter(
        Product.shopkeeper_id == shopkeeper_id,
        Product.is_deleted == False
    ).all()"""
if str3 in content:
    content = content.replace(str3, str3 + "\n    products.sort(key=lambda p: get_product_sort_key(p.name))")
    
# 4. admin page
str4 = """    products = db.query(Product).filter(Product.is_deleted == False).all()"""
if str4 in content:
    content = content.replace(str4, str4 + "\n    products.sort(key=lambda p: get_product_sort_key(p.name))")
    

open("main.py", "w", encoding="utf-8").write(content)
print("Sorting applied successfully")
