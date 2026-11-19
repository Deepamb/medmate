import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

url = os.getenv("DATABASE_URL", "sqlite:///./medmate.db")
if url.startswith("postgres://"):  # some hosts still use the old prefix
    url = url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    url,
    connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    pool_pre_ping=True,  # checks a connection is alive before using it
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)