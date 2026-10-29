import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import DATABASE_URL

engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Use NullPool for serverless / cloud PostgreSQL so connections are returned immediately
    # This prevents holding open idle connections that exhaust Supabase limits
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
