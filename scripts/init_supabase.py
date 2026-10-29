"""
Supabase Database Initialization & Diagnostics Tool for Ponnangai POS.

This script:
1. Validates connection to the database (Supabase / PostgreSQL).
2. Creates all required tables (users, products, shop_inventories, bills, bill_items, cash_transactions).
3. Verifies if an Admin user exists, creating one if empty.
4. Prints a health report of all tables and record counts.

Usage:
    python scripts/init_supabase.py
    python scripts/init_supabase.py --admin-user myadmin --admin-pass mysecurepassword
"""

import os
import sys
import argparse
from sqlalchemy import text

# Configure stdout for utf-8 if supported on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add workspace root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.core.config import DATABASE_URL
from app.models.database import Base, engine, SessionLocal
from app.models.domain import User, Product, ShopInventory, Bill, BillItem, CashTransaction
from app.core.security import pwd_context


def mask_url(url: str) -> str:
    """Mask password in connection string for display."""
    if "@" in url and "://" in url:
        prefix, rest = url.split("://", 1)
        creds, host = rest.split("@", 1)
        user = creds.split(":")[0] if ":" in creds else creds
        return f"{prefix}://{user}:****@{host}"
    return url


def run_init(admin_username: str = "admin", admin_password: str = "admin123"):
    print("=" * 60)
    print("[*] Ponnangai POS -- Supabase Database Setup")
    print("=" * 60)
    print(f"[*] Database URL: {mask_url(DATABASE_URL)}")

    # 1. Test connection
    print("\n[1/4] Testing connection to database...")
    try:
        with engine.connect() as conn:
            if "sqlite" in DATABASE_URL:
                ver = conn.execute(text("SELECT sqlite_version();")).scalar()
                server_desc = f"SQLite {ver}"
            else:
                ver = conn.execute(text("SELECT version();")).scalar()
                server_desc = ver.split(',')[0] if ver else 'PostgreSQL'
            print(f"  [+] Connected successfully!")
            print(f"  [i] Server: {server_desc}")
    except Exception as e:
        print(f"  [-] Connection failed: {e}")
        print("\nTroubleshooting Tips:")
        print("  - If using Supabase, ensure your connection string uses the Connection Pooler (port 5432 or 6543) or ends with '?sslmode=require'.")
        print("  - If your password has special characters like '@', '#', or '%', URL-encode them.")
        print("  - Check your .env file: DATABASE_URL=\"postgresql://postgres.[REF]:[PASS]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require\"")
        sys.exit(1)

    # 2. Create tables
    print("\n[2/4] Ensuring database schema and tables exist...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  [+] Schema verified / tables created successfully!")
    except Exception as e:
        print(f"  [-] Failed to create tables: {e}")
        sys.exit(1)

    # 3. Verify users & seed default admin if needed
    print("\n[3/4] Checking administrative users...")
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print(f"  [!] No users found in database.")
            print(f"  [*] Creating default Admin user: '{admin_username}'...")
            new_admin = User(
                username=admin_username,
                password=pwd_context.hash(admin_password),
                role="Admin",
                is_deleted=False
            )
            db.add(new_admin)
            db.commit()
            print(f"  [+] Admin account created!")
            print(f"      Username: {admin_username}")
            print(f"      Password: {admin_password}")
            print(f"      [!] Please change this password after logging in from the Admin panel!")
        else:
            admins = db.query(User).filter(User.role == "Admin", User.is_deleted == False).all()
            if admins:
                admin_names = [a.username for a in admins]
                print(f"  [+] Found {len(admins)} active Admin user(s): {', '.join(admin_names)}")
            else:
                print(f"  [!] Found {user_count} user(s), but no active Admin found.")
                print(f"  [*] Creating Admin user: '{admin_username}'...")
                new_admin = User(
                    username=admin_username,
                    password=pwd_context.hash(admin_password),
                    role="Admin",
                    is_deleted=False
                )
                db.add(new_admin)
                db.commit()
                print(f"  [+] Admin created successfully!")
    except Exception as e:
        print(f"  [-] Error verifying users: {e}")
        db.rollback()
    finally:
        db.close()

    # 4. Summary report
    print("\n[4/4] Database Status Report:")
    db = SessionLocal()
    try:
        models = [
            ("users", User),
            ("products", Product),
            ("shop_inventories", ShopInventory),
            ("bills", Bill),
            ("bill_items", BillItem),
            ("cash_transactions", CashTransaction),
        ]
        print("  " + "-" * 40)
        print(f"  {'Table Name':<22} | {'Row Count':<10}")
        print("  " + "-" * 40)
        for tbl, model in models:
            try:
                cnt = db.query(model).count()
                print(f"  {tbl:<22} | {cnt:<10}")
            except Exception:
                print(f"  {tbl:<22} | (error reading)")
        print("  " + "-" * 40)
    finally:
        db.close()

    print("\n[+] Supabase initialization complete! The application is ready to serve.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Supabase database for Ponnangai POS")
    parser.add_argument("--admin-user", default="admin", help="Default admin username if table is empty")
    parser.add_argument("--admin-pass", default="admin123", help="Default admin password if table is empty")
    args = parser.parse_args()

    run_init(admin_username=args.admin_user, admin_password=args.admin_pass)
