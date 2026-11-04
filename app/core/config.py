import os
import re
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip().strip("'").strip('"')

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
if SECRET_KEY:
    SECRET_KEY = SECRET_KEY.strip().strip("'").strip('"')

PRODUCTION_STR = os.getenv("PRODUCTION", "False")
if PRODUCTION_STR:
    PRODUCTION_STR = PRODUCTION_STR.strip().strip("'").strip('"')
PRODUCTION = PRODUCTION_STR.lower() == "true"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://")[0]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Ensure sslmode=require for Supabase hosts
if ("supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL) and "sslmode" not in DATABASE_URL:
    delimiter = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{delimiter}sslmode=require"

# Supabase Cloud Storage Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
if not SUPABASE_URL:
    m = re.search(r"postgres\.([a-z0-9]+):", DATABASE_URL)
    if m:
        SUPABASE_URL = f"https://{m.group(1)}.supabase.co"

SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "products")
SUPABASE_STORAGE_URL = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}" if SUPABASE_URL else ""
