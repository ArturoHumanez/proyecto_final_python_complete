from src.domain.entities import Order, OrderItem
from src.domain.exceptions import OrderNotFoundError
from src.domain.ports import EventPublisher, UnitOfWork


class CreateOrderUseCase:
    def __init__(self, uow: UnitOfWork, publisher: EventPublisher) -> None:
        self._uow = uow
        self._publisher = publisher

    def execute(self, customer: str, items: list[dict]) -> Order:
        order_items = [
            OrderItem(
                product=i["product"],
                price=i["price"],
                quantity=i.get("quantity", 1),
            )
            for i in items
        ]
        with self._uow:
            order = Order(customer=customer, items=order_items)
            saved = self._uow.orders.save(order)
            saved.mark_created()
            self._uow.commit()
            self._publisher.publish(saved.collect_events())
        return saved


class CompleteOrderUseCase:
    def __init__(self, uow: UnitOfWork, publisher: EventPublisher) -> None:
        self._uow = uow
        self._publisher = publisher

    def execute(self, order_id: int) -> Order:
        with self._uow:
            order = self._uow.orders.find_by_id(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            order.complete()
            self._uow.orders.save(order)
            self._uow.commit()
            self._publisher.publish(order.collect_events())
        return order


class CancelOrderUseCase:
    def __init__(self, uow: UnitOfWork, publisher: EventPublisher) -> None:
        self._uow = uow
        self._publisher = publisher

    def execute(self, order_id: int, reason: str = "") -> Order:
        with self._uow:
            order = self._uow.orders.find_by_id(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            order.cancel(reason=reason)
            self._uow.orders.save(order)
            self._uow.commit()
            self._publisher.publish(order.collect_events())
        return order


class GetOrderUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, order_id: int) -> Order:
        with self._uow:
            order = self._uow.orders.find_by_id(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            return order


class ListOrdersUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, status: str | None = None) -> list[Order]:
        with self._uow:
            if status:
                return self._uow.orders.find_by_status(status)
            return self._uow.orders.find_all()
