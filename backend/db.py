import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback for local development if DATABASE_URL is not set
if not DATABASE_URL:
    # Local fallback SQLite file under backend/data
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.abspath(os.path.join(DATA_DIR, 'dev.db'))}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
