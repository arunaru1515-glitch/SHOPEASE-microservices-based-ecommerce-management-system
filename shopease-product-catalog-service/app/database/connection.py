from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

database_url = settings.get_database_url()

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    database_url,
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session.
    Guarantees session is cleanly closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

