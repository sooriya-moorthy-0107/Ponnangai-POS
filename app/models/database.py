from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import DATABASE_URL

engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Resilience for cloud PostgreSQL (Supabase poolers / remote DBs)
    engine_kwargs.update({
        "pool_pre_ping": True,   # Automatically test connection liveness before query
        "pool_recycle": 300,     # Recycle connections every 5 minutes to prevent dropped connections
        "pool_size": 10,         # Sensible connection pool size
        "max_overflow": 20,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
