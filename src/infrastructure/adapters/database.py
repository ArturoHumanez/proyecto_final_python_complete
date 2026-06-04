import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.adapters.sql_models import Base
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, echo=settings.debug)

SessionFactory = sessionmaker(bind=engine)


def create_tables() -> None:
    Base.metadata.create_all(engine)
    logger.info("Tablas creadas en %s", settings.database_url)


def get_session() -> Session:
    return SessionFactory()
