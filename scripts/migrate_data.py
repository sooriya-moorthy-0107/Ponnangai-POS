"""
Data Migration Tool: AWS RDS / SQLite -> Supabase PostgreSQL.

Migrates all application data preserving primary keys and resets PostgreSQL
serial sequences on the target database.

Usage:
    python scripts/migrate_data.py --source "<source_url>" --target "<target_url>"
    # Or rely on SOURCE_DATABASE_URL and DATABASE_URL in .env:
    python scripts/migrate_data.py
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text, MetaData, Table

# Configure stdout for utf-8 if supported on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add workspace root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.models.database import Base
import app.models.domain  # noqa: F401 - registers tables with Base.metadata


TABLES_IN_ORDER = [
    "users",
    "products",
    "shop_inventories",
    "bills",
    "bill_items",
    "cash_transactions",
]


def clean_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if ("supabase.co" in url or "pooler.supabase.com" in url) and "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def mask_url(url: str) -> str:
    if "@" in url and "://" in url:
        prefix, rest = url.split("://", 1)
        creds, host = rest.split("@", 1)
        user = creds.split(":")[0] if ":" in creds else creds
        return f"{prefix}://{user}:****@{host}"
    return url


def migrate(source_url: str, target_url: str, clear_target: bool = False):
    source_url = clean_url(source_url)
    target_url = clean_url(target_url)

    print("=" * 65)
    print("[*] Ponnangai POS -- Database Migration Tool")
    print("=" * 65)
    print(f" Source (AWS RDS / Source DB): {mask_url(source_url)}")
    print(f" Target (Supabase):            {mask_url(target_url)}")
    print("=" * 65)

    source_kwargs = {"connect_args": {"check_same_thread": False}} if "sqlite" in source_url else {}
    target_kwargs = {"connect_args": {"check_same_thread": False}} if "sqlite" in target_url else {"pool_pre_ping": True}

    source_engine = create_engine(source_url, **source_kwargs)
    target_engine = create_engine(target_url, **target_kwargs)

    # 1. Ensure target schema exists
    print("\n[1/3] Ensuring tables exist in target Supabase database...")
    Base.metadata.create_all(bind=target_engine)
    print("  [+] Target schema ready.")

    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)

    target_meta = MetaData()
    target_meta.reflect(bind=target_engine)

    # 2. Transfer tables in dependency order
    print("\n[2/3] Migrating data...")
    with source_engine.connect() as src_conn, target_engine.begin() as tgt_conn:
        if clear_target:
            print("  [!] Clearing existing data in target (in reverse dependency order)...")
            for table_name in reversed(TABLES_IN_ORDER):
                if table_name in target_meta.tables:
                    tgt_conn.execute(target_meta.tables[table_name].delete())

        for table_name in TABLES_IN_ORDER:
            if table_name not in source_meta.tables or table_name not in target_meta.tables:
                print(f"  [>] Skipping '{table_name}' (not found in schema)")
                continue

            src_table = source_meta.tables[table_name]
            tgt_table = target_meta.tables[table_name]

            # Read from source
            rows = src_conn.execute(src_table.select()).mappings().all()
            if not rows:
                print(f"  [i] Table '{table_name}': 0 rows (empty)")
                continue

            # Insert into target
            inserted = 0
            valid_cols = set(tgt_table.columns.keys())
            for row in rows:
                data = {k: v for k, v in dict(row).items() if k in valid_cols}
                # Check if row with primary key already exists
                pk_col = list(src_table.primary_key.columns)[0].name
                if pk_col in data:
                    existing = tgt_conn.execute(
                        tgt_table.select().where(tgt_table.c[pk_col] == data[pk_col])
                    ).first()
                    if not existing:
                        tgt_conn.execute(tgt_table.insert().values(**data))
                        inserted += 1
                else:
                    tgt_conn.execute(tgt_table.insert().values(**data))
                    inserted += 1

            print(f"  [+] Table '{table_name}': {len(rows)} source rows -> {inserted} newly inserted")

    # 3. Reset PostgreSQL serial sequences on target so future inserts work seamlessly
    print("\n[3/3] Synchronizing PostgreSQL serial sequences on Supabase...")
    if "postgresql" in target_url:
        with target_engine.begin() as conn:
            for table_name in TABLES_IN_ORDER:
                try:
                    query = f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table_name}', 'id'),
                            COALESCE((SELECT MAX(id) FROM "{table_name}"), 1),
                            true
                        );
                    """
                    conn.execute(text(query))
                    print(f"  [~] Sequence reset for '{table_name}'")
                except Exception:
                    # Ignore if sequence doesn't exist or table has no id sequence
                    pass

    print("\n[+] Migration completed successfully!")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Migrate data from AWS RDS/SQLite to Supabase")
    parser.add_argument("--source", default=os.getenv("SOURCE_DATABASE_URL", os.getenv("DATABASE_URL")), help="Source Database URL (e.g., AWS RDS or sqlite:///test.db)")
    parser.add_argument("--target", default=os.getenv("TARGET_DATABASE_URL", os.getenv("DATABASE_URL")), help="Target Database URL (Supabase)")
    parser.add_argument("--clear-target", action="store_true", help="Clear target tables before inserting")
    args = parser.parse_args()

    if not args.source or not args.target:
        print("[-] Error: Both source and target URLs are required.")
        print("Usage: python scripts/migrate_data.py --source <RDS_URL> --target <SUPABASE_URL>")
        sys.exit(1)

    if args.source == args.target:
        print("[-] Error: Source and Target URLs cannot be identical.")
        print("Please provide distinct --source and --target database URLs.")
        sys.exit(1)

    migrate(args.source, args.target, clear_target=args.clear_target)
