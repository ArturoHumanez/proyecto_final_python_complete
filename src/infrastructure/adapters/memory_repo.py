from src.domain.entities import Order


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[int, Order] = {}
        self._next_id = 1

    def save(self, order: Order) -> Order:
        if order.id is None:
            order.id = self._next_id
            self._next_id += 1
        self._orders[order.id] = order
        return order

    def find_by_id(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def find_all(self) -> list[Order]:
        return list(self._orders.values())

    def find_by_status(self, status: str) -> list[Order]:
        return [o for o in self._orders.values() if o.status == status]

    def delete(self, order_id: int) -> bool:
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False
