from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from job_hunt_api.config import get_settings


def create_database_engine() -> Engine:
    return create_engine(
        str(get_settings().database_url),
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create connections lazily so non-database routes can still start."""
    return sessionmaker(bind=create_database_engine(), autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
