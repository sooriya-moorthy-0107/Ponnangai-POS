import re

with open("main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

target_factory_products = """    # Fetch ALL active products for factory cashier so everything is visible
    products = db.query(Product).filter(
        Product.is_deleted == False
    ).all()"""
replacement_factory_products = """    # Fetch products active for this factory cashier
    products = db.query(Product).filter(
        Product.shopkeeper_id == target_cashier_id,
        Product.is_deleted == False
    ).all()"""

main_py = main_py.replace(target_factory_products, replacement_factory_products)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py)
