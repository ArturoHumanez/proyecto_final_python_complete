import logging
from typing import Any

from sqlalchemy.orm import Session

from src.infrastructure.adapters.database import SessionFactory
from src.infrastructure.adapters.sql_repo import SqlOrderRepository

logger = logging.getLogger(__name__)


class SqlUnitOfWork:
    orders: Any

    def __enter__(self) -> "SqlUnitOfWork":
        self._session: Session = SessionFactory()
        self.orders = SqlOrderRepository(self._session)
        logger.debug("UoW: transacción abierta")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self.rollback()
            logger.warning("UoW: rollback por excepción — %s", exc_val)
        self._session.close()
        logger.debug("UoW: sesión cerrada")

    def commit(self) -> None:
        self._session.commit()
        logger.debug("UoW: commit exitoso")

    def rollback(self) -> None:
        self._session.rollback()
        logger.debug("UoW: rollback ejecutado")
