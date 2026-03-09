from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ltt_core.config import get_settings


def _build_engine():
    settings = get_settings()
    return create_engine(settings.DATABASE_URL)


def get_session():
    engine = _build_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()