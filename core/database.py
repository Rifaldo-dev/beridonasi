from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_NAME
from .base import Base

DATABASE_URL = f"sqlite:///{DATABASE_NAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
