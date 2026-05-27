import sys

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Chunk 5: admin page
target_admin = """    # Fetch historical factory sessions for reports
    factory_sessions = db.query(FactorySession).order_by(FactorySession.start_time.desc()).all()
    
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
        "shop_performance": shop_performance,
        "factory_sessions": factory_sessions
    })"""
replacement_admin = """    return templates.TemplateResponse(request=request, name="admin.html", context={
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
    })"""
content = content.replace(target_admin, replacement_admin)

# Chunk 6: api/bills create
target_bills = """    is_factory = (sk_user.role == "Factory")
    factory_session = None
    if is_factory:
        factory_session = db.query(FactorySession).filter(
            FactorySession.cashier_id == target_shopkeeper_id,
            FactorySession.status == "open"
        ).first()
        if not factory_session:
            return JSONResponse(
                status_code=400,
                content={"detail": "No active open shift/session found. Please start the day before making sales."}
            )
            
    # Pass 1: Validate available stock for all items (ONLY for non-factory shops)
    if not is_factory:
        for item in data.get("items", []):
            product = db.query(Product).filter(Product.id == item["id"]).first()
            if not product:
                continue
                
            shop_inv = db.query(ShopInventory).filter(
                ShopInventory.shopkeeper_id == target_shopkeeper_id,
                ShopInventory.product_id == product.id
            ).first()
            
            current_stock = shop_inv.stock if shop_inv else 0
            if current_stock < item["qty"]:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Insufficient stock for '{product.name}'. Only {current_stock} left, but {item['qty']} were requested."}
                )
            
    # Pass 2: Deduct stock or record factory balance and compile bill items
    for item in data.get("items", []):
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            continue
            
        qty_float = float(item["qty"])
        custom_price = float(item.get("price", product.price))
        
        if is_factory:
            # Factory role does not use ShopInventory, record in FactorySessionBalance instead
            session_bal = db.query(FactorySessionBalance).filter(
                FactorySessionBalance.session_id == factory_session.id,
                FactorySessionBalance.product_id == product.id
            ).first()
            if not session_bal:
                session_bal = FactorySessionBalance(
                    session_id=factory_session.id,
                    product_id=product.id,
                    opening_balance=0.0,
                    quantity_sold=qty_float,
                    closing_balance=-qty_float
                )
                db.add(session_bal)
            else:
                session_bal.quantity_sold += qty_float
                session_bal.closing_balance = session_bal.opening_balance - session_bal.quantity_sold
                session_bal.discrepancy = session_bal.actual_balance - session_bal.closing_balance
        else:
            # Standard Shopkeeper: deduct from traditional inventory
            shop_inv = db.query(ShopInventory).filter(
                ShopInventory.shopkeeper_id == target_shopkeeper_id, 
                ShopInventory.product_id == product.id
            ).first()
            if shop_inv:
                shop_inv.stock -= int(item["qty"])"""
replacement_bills = """    # Pass 1: Validate available stock for all items
    for item in data.get("items", []):
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            continue
            
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == target_shopkeeper_id,
            ShopInventory.product_id == product.id
        ).first()
        
        current_stock = shop_inv.stock if shop_inv else 0
        if current_stock < item["qty"]:
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
        if shop_inv:
            shop_inv.stock -= int(item["qty"])"""
content = content.replace(target_bills, replacement_bills)

# Chunk 7: api/bills revert
target_revert = """    bill_cashier = db.query(User).filter(User.id == bill.cashier_id).first()
    is_factory = (bill_cashier.role == "Factory") if bill_cashier else False
    
    # We find active factory session if is_factory
    factory_session = None
    if is_factory:
        factory_session = db.query(FactorySession).filter(
            FactorySession.cashier_id == bill.cashier_id,
            FactorySession.status == "open"
        ).first()
        
    items_data = []
    # Revert stock and prepare cart data
    for item in bill.items:
        max_stock = 9999.0 # Default fallback for loose sales in UI
        if is_factory:
            if factory_session:
                session_bal = db.query(FactorySessionBalance).filter(
                    FactorySessionBalance.session_id == factory_session.id,
                    FactorySessionBalance.product_id == item.product_id
                ).first()
                if session_bal:
                    session_bal.quantity_sold -= item.quantity
                    session_bal.closing_balance = session_bal.opening_balance - session_bal.quantity_sold
                    session_bal.discrepancy = session_bal.actual_balance - session_bal.closing_balance
        else:
            # Restore stock in shop inventory
            shop_inv = db.query(ShopInventory).filter(
                ShopInventory.shopkeeper_id == bill.cashier_id,
                ShopInventory.product_id == item.product_id
            ).first()
            if shop_inv:
                shop_inv.stock += int(item.quantity)
                max_stock = float(shop_inv.stock)"""
replacement_revert = """    items_data = []
    # Revert stock and prepare cart data
    for item in bill.items:
        max_stock = 9999.0 # Default fallback for loose sales in UI
        # Restore stock in shop inventory
        shop_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == bill.cashier_id,
            ShopInventory.product_id == item.product_id
        ).first()
        if shop_inv:
            shop_inv.stock += int(item.quantity)
            max_stock = float(shop_inv.stock)"""
content = content.replace(target_revert, replacement_revert)

# Chunk 8: reset
target_reset = """    if dialect == 'sqlite':
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(ShopInventory).delete()
        db.query(Product).delete()
        db.query(FactorySessionBalance).delete()
        db.query(FactorySession).delete()
        db.query(User).filter(User.is_deleted == True).delete()
        try:
            db.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('bill_items', 'bills', 'shop_inventories', 'products', 'factory_session_balances', 'factory_sessions')"))
        except Exception:
            pass
    elif dialect in ['postgresql', 'postgres']:
        db.query(User).filter(User.is_deleted == True).delete()
        db.execute(text("TRUNCATE TABLE bill_items, bills, shop_inventories, products, factory_session_balances, factory_sessions RESTART IDENTITY CASCADE"))
    else:
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(ShopInventory).delete()
        db.query(Product).delete()
        db.query(FactorySessionBalance).delete()
        db.query(FactorySession).delete()
        db.query(User).filter(User.is_deleted == True).delete()"""
replacement_reset = """    if dialect == 'sqlite':
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
        db.query(User).filter(User.is_deleted == True).delete()
        db.execute(text("TRUNCATE TABLE bill_items, bills, shop_inventories, products RESTART IDENTITY CASCADE"))
    else:
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(ShopInventory).delete()
        db.query(Product).delete()
        db.query(User).filter(User.is_deleted == True).delete()"""
content = content.replace(target_reset, replacement_reset)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)
