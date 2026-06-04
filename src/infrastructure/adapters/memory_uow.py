from typing import Any

from src.infrastructure.adapters.memory_repo import InMemoryOrderRepository


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.orders: Any = InMemoryOrderRepository()
        self._committed = False

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._committed = False
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._committed and exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        self._committed = False
