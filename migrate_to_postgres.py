import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Append current directory so we can import from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# SQLite Engine Setup
sqlite_url = "sqlite:///./ponnangai_pos.db"
if not os.path.exists("./ponnangai_pos.db"):
    print("Warning: SQLite database not found at standard path ./ponnangai_pos.db")
sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
SQLiteSession = sessionmaker(bind=sqlite_engine)

# Postgres Engine Setup
# By default, we point to localhost:5432 as mapped by the Docker Postgres container.
default_postgres_url = "postgresql://pos_user:pos_password@localhost:5432/ponnangai_pos"
postgres_url = os.getenv("POSTGRES_DATABASE_URL", os.getenv("DATABASE_URL", default_postgres_url))

if postgres_url.startswith("postgres://"):
    postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

print(f"Connecting to SQLite: {sqlite_url}")
print(f"Connecting to PostgreSQL: {postgres_url}")

try:
    postgres_engine = create_engine(postgres_url)
    with postgres_engine.connect() as conn:
        pass
except Exception as e:
    print("\n[ERROR] Could not connect to PostgreSQL database!")
    print("Is your Docker PostgreSQL container running? If not, run:")
    print("  docker compose up -d db")
    print(f"\nConnection Error Details: {e}")
    sys.exit(1)

PostgresSession = sessionmaker(bind=postgres_engine)

# Import models from main
from main import Base, User, Product, ShopInventory, Bill, BillItem

def migrate():
    print("\nEnsuring all tables are created in PostgreSQL...")
    Base.metadata.create_all(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    # 1. Migrate Users
    try:
        users = sqlite_session.query(User).all()
        print(f"Found {len(users)} users in SQLite.")
        for u in users:
            existing = postgres_session.query(User).filter(User.id == u.id).first()
            if not existing:
                postgres_session.add(User(id=u.id, username=u.username, password=u.password, role=u.role))
        postgres_session.commit()
        print("Users migration complete.")
    except Exception as e:
        postgres_session.rollback()
        print(f"[ERROR] Failed to migrate Users: {e}")

    # 2. Migrate Products
    try:
        products = sqlite_session.query(Product).all()
        print(f"Found {len(products)} products in SQLite.")
        for p in products:
            existing = postgres_session.query(Product).filter(Product.id == p.id).first()
            if not existing:
                postgres_session.add(Product(id=p.id, name=p.name, price=p.price, image_filename=p.image_filename))
        postgres_session.commit()
        print("Products migration complete.")
    except Exception as e:
        postgres_session.rollback()
        print(f"[ERROR] Failed to migrate Products: {e}")

    # 3. Migrate ShopInventory
    try:
        inventories = sqlite_session.query(ShopInventory).all()
        print(f"Found {len(inventories)} inventory items in SQLite.")
        for inv in inventories:
            existing = postgres_session.query(ShopInventory).filter(ShopInventory.id == inv.id).first()
            if not existing:
                postgres_session.add(ShopInventory(
                    id=inv.id,
                    shopkeeper_id=inv.shopkeeper_id,
                    product_id=inv.product_id,
                    stock=inv.stock
                ))
        postgres_session.commit()
        print("ShopInventory migration complete.")
    except Exception as e:
        postgres_session.rollback()
        print(f"[ERROR] Failed to migrate ShopInventory: {e}")

    # 4. Migrate Bills
    try:
        bills = sqlite_session.query(Bill).all()
        print(f"Found {len(bills)} bills in SQLite.")
        for b in bills:
            existing = postgres_session.query(Bill).filter(Bill.id == b.id).first()
            if not existing:
                postgres_session.add(Bill(
                    id=b.id,
                    total_amount=b.total_amount,
                    discount=b.discount,
                    final_amount=b.final_amount,
                    payment_mode=b.payment_mode,
                    timestamp=b.timestamp,
                    cashier_id=b.cashier_id,
                    cashier_name=b.cashier_name
                ))
        postgres_session.commit()
        print("Bills migration complete.")
    except Exception as e:
        postgres_session.rollback()
        print(f"[ERROR] Failed to migrate Bills: {e}")

    # 5. Migrate BillItems
    try:
        bill_items = sqlite_session.query(BillItem).all()
        print(f"Found {len(bill_items)} bill items in SQLite.")
        for item in bill_items:
            existing = postgres_session.query(BillItem).filter(BillItem.id == item.id).first()
            if not existing:
                postgres_session.add(BillItem(
                    id=item.id,
                    bill_id=item.bill_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_sale=item.price_at_sale
                ))
        postgres_session.commit()
        print("BillItems migration complete.")
    except Exception as e:
        postgres_session.rollback()
        print(f"[ERROR] Failed to migrate BillItems: {e}")

    # 6. Reset PostgreSQL sequence generators (so AUTO-INCREMENT starts after migrated IDs)
    tables = ['users', 'products', 'shop_inventories', 'bills', 'bill_items']
    print("\nUpdating primary key sequence generators in PostgreSQL...")
    with postgres_engine.connect() as conn:
        for table in tables:
            try:
                res = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table}"))
                max_id = res.scalar()
                if max_id > 0:
                    conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id})"))
                    print(f"  - Reset auto-increment sequence for table '{table}' to {max_id}")
            except Exception as seq_err:
                print(f"  - Warning: Could not reset sequence for table '{table}': {seq_err}")
        conn.execute(text("COMMIT"))

    print("\nDatabase migration completed successfully!")
    sqlite_session.close()
    postgres_session.close()

if __name__ == "__main__":
    migrate()
