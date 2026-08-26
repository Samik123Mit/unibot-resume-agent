import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def normalize_database_url(url: str) -> str:
    """Route generic managed-Postgres URLs through the installed Psycopg 3 driver."""
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./unibot.db"))
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
