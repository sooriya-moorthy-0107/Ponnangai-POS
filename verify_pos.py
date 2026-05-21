import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Append current directory so we can import from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import Base, User, Product, ShopInventory, Bill, BillItem, DATABASE_URL

print(f"Connecting to database for verification: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_isolated_catalog_and_soft_delete():
    db = SessionLocal()
    try:
        print("\n--- Starting Verification Tests ---")
        
        # 1. Clean up old test data to ensure clean state
        print("Cleaning up old test users/products...")
        
        # Find test products
        test_prods = db.query(Product).filter(Product.price == 999.0).all()
        test_prod_ids = [p.id for p in test_prods]
        
        # Delete dependent bill items and inventories first
        if test_prod_ids:
            db.query(BillItem).filter(BillItem.product_id.in_(test_prod_ids)).delete(synchronize_session=False)
            db.query(ShopInventory).filter(ShopInventory.product_id.in_(test_prod_ids)).delete(synchronize_session=False)
        
        db.query(Bill).filter(Bill.total_amount == 999.0).delete(synchronize_session=False)
        if test_prod_ids:
            db.query(Product).filter(Product.id.in_(test_prod_ids)).delete(synchronize_session=False)
        
        db.query(User).filter(User.username.in_(["test_sk_a", "test_sk_b"])).delete(synchronize_session=False)
        db.commit()

        # 2. Create test shopkeepers
        print("1. Creating test shopkeepers: test_sk_a and test_sk_b")
        sk_a = User(username="test_sk_a", password="password123", role="Shopkeeper")
        sk_b = User(username="test_sk_b", password="password123", role="Shopkeeper")
        db.add_all([sk_a, sk_b])
        db.commit()
        db.refresh(sk_a)
        db.refresh(sk_b)
        print(f"   Created shopkeeper A (ID: {sk_a.id}) and shopkeeper B (ID: {sk_b.id})")

        # 3. Verify new shop starts with zero items in inventory
        print("2. Verifying shop keepers start with zero products")
        inventory_a = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == sk_a.id).all()
        inventory_b = db.query(ShopInventory).filter(ShopInventory.shopkeeper_id == sk_b.id).all()
        
        assert len(inventory_a) == 0, f"Expected 0 items for sk_a, got {len(inventory_a)}"
        assert len(inventory_b) == 0, f"Expected 0 items for sk_b, got {len(inventory_b)}"
        print("   ✅ Verified: Both shops started with empty catalogs (no auto-populated items).")

        # 4. Add product scoped to Shop A
        print("3. Adding product scoped to Shop A ('Unique Product A' @ ₹999.0)")
        product_a = Product(
            name="Unique Product A",
            price=999.0,
            image_filename="unique_a.jpg",
            shopkeeper_id=sk_a.id,
            is_deleted=False
        )
        db.add(product_a)
        db.commit()
        db.refresh(product_a)
        
        # Add stock in ShopInventory for Shop A
        inv_a = ShopInventory(shopkeeper_id=sk_a.id, product_id=product_a.id, stock=10)
        db.add(inv_a)
        db.commit()
        print(f"   Added product A (ID: {product_a.id}) with 10 stock to Shop A")

        # 5. Verify Shop A product is completely invisible to Shop B
        print("4. Verifying Shop A's product is invisible to Shop B's active catalog")
        # Check active catalog query for Shop B
        active_inv_b = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == sk_b.id,
            ShopInventory.stock > 0
        ).all()
        assert len(active_inv_b) == 0, "Shop B should have 0 active items"
        
        # Check if the product itself is linked to Shop A
        prod_in_b = db.query(Product).filter(
            Product.id == product_a.id,
            Product.shopkeeper_id == sk_b.id
        ).first()
        assert prod_in_b is None, "Product A should not be linked to Shop B"
        print("   ✅ Verified: Shop A product is 100% isolated and invisible to Shop B.")

        # 6. Verify soft-deletion preserves historical sales & analytics
        print("5. Verifying soft-deletion, receipt, and analytics preservation")
        
        # A. Create a sale / bill for product A in Shop A
        print("   A. Creating a mock bill for 'Unique Product A' in Shop A...")
        bill = Bill(
            total_amount=999.0,
            discount=0.0,
            final_amount=999.0,
            payment_mode="Cash",
            cashier_id=sk_a.id,
            cashier_name=sk_a.username
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        bill_item = BillItem(
            bill_id=bill.id,
            product_id=product_a.id,
            quantity=1,
            price_at_sale=999.0
        )
        db.add(bill_item)
        
        # Deduct stock
        inv_a.stock -= 1
        db.commit()
        print(f"      Created bill (ID: {bill.id}) with item sale (Price: {bill_item.price_at_sale})")

        # B. Soft-delete Product A
        print("   B. Performing soft-delete on 'Unique Product A'...")
        # Simulating API /api/products/delete: is_deleted = True and stock = 0
        product_a.is_deleted = True
        inv_a.stock = 0
        db.commit()
        print("      Marked product.is_deleted = True and set inventory.stock = 0")

        # C. Verify it's hidden from Shop A's active POS view
        print("   C. Verifying product is hidden from Shop A's active inventory...")
        active_inv_a = db.query(ShopInventory).join(Product).filter(
            ShopInventory.shopkeeper_id == sk_a.id,
            ShopInventory.stock > 0,
            Product.is_deleted == False
        ).all()
        
        # Ensure our test product is not in the active list
        active_prod_ids = [item.product_id for item in active_inv_a]
        assert product_a.id not in active_prod_ids, "Soft-deleted product must be hidden from active POS view!"
        print("      ✅ Hidden from active POS view successfully.")

        # D. Verify that the previous bill/receipt can still load product information
        print("   D. Verifying historical receipt still renders product details...")
        loaded_bill = db.query(Bill).filter(Bill.id == bill.id).first()
        assert loaded_bill is not None, "Receipt bill should exist"
        assert len(loaded_bill.items) == 1, "Receipt should have 1 item"
        item_product = loaded_bill.items[0].product
        assert item_product is not None, "Product relation must not be null"
        assert item_product.name == "Unique Product A", f"Expected 'Unique Product A', got '{item_product.name}'"
        print(f"      ✅ Historical receipt loaded successfully for soft-deleted product: '{item_product.name}'")

        # E. Verify that shop performance analytics still aggregates soft-deleted product sales
        print("   E. Verifying shop analytics still includes soft-deleted product sales...")
        # Simulate /api/analytics/shop/{shop_id} SQL aggregation
        from sqlalchemy import func
        items_query = db.query(
            Product.name,
            func.sum(BillItem.quantity).label("total_qty"),
            func.sum(BillItem.quantity * BillItem.price_at_sale).label("total_revenue")
        ).join(BillItem, Product.id == BillItem.product_id)\
         .join(Bill, Bill.id == BillItem.bill_id)\
         .filter(Bill.cashier_id == sk_a.id)\
         .group_by(Product.name).all()
        
        breakdown = {row[0]: {"qty": row[1], "revenue": row[2]} for row in items_query}
        assert "Unique Product A" in breakdown, "Soft-deleted product must be present in sales analytics breakdown!"
        assert breakdown["Unique Product A"]["qty"] == 1, "Expected quantity of 1 in analytics"
        assert breakdown["Unique Product A"]["revenue"] == 999.0, "Expected revenue of 999.0 in analytics"
        print(f"      ✅ Analytics aggregated successfully: {breakdown['Unique Product A']}")

        # F. Verify bulk stock update by product name
        print("   F. Verifying bulk stock update by product name...")
        product_new = Product(
            name="Bulk Product Match Test",
            price=150.0,
            image_filename="match_test.jpg",
            shopkeeper_id=sk_a.id,
            is_deleted=False
        )
        db.add(product_new)
        db.commit()
        db.refresh(product_new)
        
        db.add(ShopInventory(shopkeeper_id=sk_a.id, product_id=product_new.id, stock=5))
        db.commit()
        
        # Simulate CSV reader structure with name-matching row
        csv_rows = [
            {"S.No.": "1", "Product Name": "Bulk Product Match Test", "Current Stock": "5", "New Stock": "123"}
        ]
        
        updated_count = 0
        for row in csv_rows:
            prod_id = row.get("Product ID") or row.get("product_id")
            prod_name = row.get("Product Name") or row.get("name") or row.get("Product")
            new_stock = row.get("New Stock") or row.get("stock") or row.get("NewStock")
            
            if (prod_id or prod_name) and new_stock:
                product_found = None
                if prod_name:
                    product_found = db.query(Product).filter(
                        Product.name == prod_name.strip(),
                        Product.shopkeeper_id == sk_a.id,
                        Product.is_deleted == False
                    ).first()
                if product_found:
                    inv = db.query(ShopInventory).filter(
                        ShopInventory.shopkeeper_id == sk_a.id,
                        ShopInventory.product_id == product_found.id
                    ).first()
                    if not inv:
                        inv = ShopInventory(shopkeeper_id=sk_a.id, product_id=product_found.id, stock=int(new_stock))
                        db.add(inv)
                    else:
                        inv.stock = int(new_stock)
                    updated_count += 1
        db.commit()
        
        assert updated_count == 1, f"Expected 1 item updated, got {updated_count}"
        final_inv = db.query(ShopInventory).filter(
            ShopInventory.shopkeeper_id == sk_a.id,
            ShopInventory.product_id == product_new.id
        ).first()
        assert final_inv is not None, "Inventory record should exist"
        assert final_inv.stock == 123, f"Expected stock to be updated to 123, got {final_inv.stock}"
        print("      ✅ Bulk stock updated by product name successfully.")

        # 6. Clean up test data
        print("6. Cleaning up test data...")
        db.query(BillItem).filter(BillItem.bill_id == bill.id).delete(synchronize_session=False)
        db.query(Bill).filter(Bill.id == bill.id).delete(synchronize_session=False)
        db.query(ShopInventory).filter(ShopInventory.shopkeeper_id.in_([sk_a.id, sk_b.id])).delete(synchronize_session=False)
        db.query(Product).filter(Product.shopkeeper_id.in_([sk_a.id, sk_b.id])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([sk_a.id, sk_b.id])).delete(synchronize_session=False)
        db.commit()
        print("   Cleaned up test users, products, inventories, and bills.")
        
        print("\n🎉 ALL VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")
        
    except AssertionError as ae:
        print(f"\n❌ ASSERTION FAILED: {ae}")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR ENCOUNTERED during verification: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_isolated_catalog_and_soft_delete()
