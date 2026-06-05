import pytest

from src.domain.entities import Order, OrderItem
from src.domain.events import OrderCancelled, OrderCompleted, OrderCreated
from src.domain.exceptions import InvalidOrderError, OrderStateError


class TestOrderItem:
    def test_subtotal(self):
        item = OrderItem(product="Laptop", price=25000, quantity=2)
        assert item.subtotal == 50000

    def test_negative_price_raises(self):
        with pytest.raises(InvalidOrderError, match="positivo"):
            OrderItem(product="Laptop", price=-5, quantity=1)

    def test_zero_quantity_raises(self):
        with pytest.raises(InvalidOrderError, match=">= 1"):
            OrderItem(product="Laptop", price=100, quantity=0)

    def test_empty_product_raises(self):
        with pytest.raises(InvalidOrderError, match="vacío"):
            OrderItem(product="  ", price=100, quantity=1)


class TestOrder:
    @pytest.fixture
    def items(self):
        return [
            OrderItem(product="Laptop", price=25000, quantity=1),
            OrderItem(product="Mouse", price=350, quantity=2),
        ]

    def test_total(self, items):
        order = Order(customer="Juan", items=items)
        assert order.total == 25700

    def test_item_count(self, items):
        order = Order(customer="Juan", items=items)
        assert order.item_count == 3

    def test_default_status_is_pending(self, items):
        order = Order(customer="Juan", items=items)
        assert order.status == "pending"

    def test_empty_customer_raises(self, items):
        with pytest.raises(InvalidOrderError, match="vacío"):
            Order(customer="", items=items)

    def test_empty_items_raises(self):
        with pytest.raises(InvalidOrderError, match="al menos un item"):
            Order(customer="Juan", items=[])

    def test_invalid_status_raises(self, items):
        with pytest.raises(InvalidOrderError, match="inválido"):
            Order(customer="Juan", items=items, status="shipped")


class TestOrderTransitions:
    @pytest.fixture
    def order(self):
        return Order(
            customer="Juan",
            items=[OrderItem(product="Laptop", price=25000, quantity=1)],
        )

    def test_complete(self, order):
        order.complete()
        assert order.status == "completed"

    def test_cancel(self, order):
        order.cancel(reason="cambié de opinión")
        assert order.status == "cancelled"

    def test_cannot_complete_cancelled(self, order):
        order.cancel()
        with pytest.raises(OrderStateError, match="cancelled.*completed"):
            order.complete()

    def test_cannot_cancel_completed(self, order):
        order.complete()
        with pytest.raises(OrderStateError, match="completed.*cancelled"):
            order.cancel()

    def test_cannot_complete_twice(self, order):
        order.complete()
        with pytest.raises(OrderStateError):
            order.complete()


class TestOrderEvents:
    @pytest.fixture
    def order(self):
        return Order(
            id=1,
            customer="Juan",
            items=[OrderItem(product="Laptop", price=25000, quantity=1)],
        )

    def test_mark_created_emits_event(self, order):
        order.mark_created()
        events = order.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], OrderCreated)
        assert events[0].customer == "Juan"
        assert events[0].total == 25000

    def test_complete_emits_event(self, order):
        order.complete()
        events = order.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], OrderCompleted)

    def test_cancel_emits_event_with_reason(self, order):
        order.cancel(reason="sin stock")
        events = order.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], OrderCancelled)
        assert events[0].reason == "sin stock"

    def test_collect_events_clears_list(self, order):
        order.mark_created()
        order.collect_events()

        assert order.collect_events() == []
