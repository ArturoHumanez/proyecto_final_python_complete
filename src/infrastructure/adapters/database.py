import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.adapters.sql_models import Base
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, echo=settings.debug)

SessionFactory = sessionmaker(bind=engine)


def create_tables(target_engine=None) -> None:
    e = target_engine or engine
    Base.metadata.create_all(e)
    logger.info("Tablas creadas")


def get_session() -> Generator[Session, None, None]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
