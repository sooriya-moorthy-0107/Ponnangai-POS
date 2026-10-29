import os
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

# Supabase Pooler: Automatically upgrade Session mode (port 5432) to Transaction mode (port 6543)
# This prevents EMAXCONNSESSION (max clients reached in session mode: 15) in serverless environments
if "pooler.supabase.com:5432" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("pooler.supabase.com:5432", "pooler.supabase.com:6543")

# Supabase requires an SSL connection; enforce sslmode=require for Supabase hosts
if ("supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL) and "sslmode" not in DATABASE_URL:
    delimiter = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{delimiter}sslmode=require"
