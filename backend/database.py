import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Using standard fallback if env var is missing during local dev
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:123456@localhost:5432/ChatApp"
)

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a customized Session 000
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
