import pytest

from src.application.event_handlers import EventBus
from src.application.use_cases import (
    CancelOrderUseCase,
    CompleteOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from src.domain.events import OrderCancelled, OrderCompleted, OrderCreated
from src.domain.exceptions import OrderNotFoundError
from src.infrastructure.adapters.memory_uow import InMemoryUnitOfWork

SAMPLE_ITEMS = [
    {"product": "Laptop", "price": 25000, "quantity": 1},
    {"product": "Mouse", "price": 350, "quantity": 2},
]


@pytest.fixture
def uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def captured_events():
    return []


@pytest.fixture
def bus(captured_events):
    bus = EventBus()
    bus.register(OrderCreated, lambda e: captured_events.append(e))
    bus.register(OrderCompleted, lambda e: captured_events.append(e))
    bus.register(OrderCancelled, lambda e: captured_events.append(e))
    return bus


class TestCreateOrder:
    def test_creates_pending_order(self, uow, bus):
        uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = uc.execute("Juan", SAMPLE_ITEMS)

        assert order.id is not None
        assert order.status == "pending"
        assert order.total == 25700

    def test_persists_in_repo(self, uow, bus):
        uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = uc.execute("Juan", SAMPLE_ITEMS)

        found = uow.orders.find_by_id(order.id)
        assert found is not None
        assert found.customer == "Juan"

    def test_emits_created_event(self, uow, bus, captured_events):
        uc = CreateOrderUseCase(uow=uow, publisher=bus)
        uc.execute("Juan", SAMPLE_ITEMS)

        assert len(captured_events) == 1
        assert isinstance(captured_events[0], OrderCreated)
        assert captured_events[0].total == 25700


class TestCompleteOrder:
    def test_completes_order(self, uow, bus):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = create_uc.execute("Juan", SAMPLE_ITEMS)

        complete_uc = CompleteOrderUseCase(uow=uow, publisher=bus)
        completed = complete_uc.execute(order.id)

        assert completed.status == "completed"

    def test_emits_completed_event(self, uow, bus, captured_events):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = create_uc.execute("Juan", SAMPLE_ITEMS)

        complete_uc = CompleteOrderUseCase(uow=uow, publisher=bus)
        complete_uc.execute(order.id)

        assert any(isinstance(e, OrderCompleted) for e in captured_events)

    def test_not_found_raises(self, uow, bus):
        uc = CompleteOrderUseCase(uow=uow, publisher=bus)
        with pytest.raises(OrderNotFoundError):
            uc.execute(999)


class TestCancelOrder:
    def test_cancels_with_reason(self, uow, bus, captured_events):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = create_uc.execute("Juan", SAMPLE_ITEMS)

        cancel_uc = CancelOrderUseCase(uow=uow, publisher=bus)
        cancelled = cancel_uc.execute(order.id, reason="sin stock")

        assert cancelled.status == "cancelled"
        cancel_event = [e for e in captured_events if isinstance(e, OrderCancelled)]
        assert cancel_event[0].reason == "sin stock"

    def test_not_found_raises(self, uow, bus):
        uc = CancelOrderUseCase(uow=uow, publisher=bus)
        with pytest.raises(OrderNotFoundError):
            uc.execute(999)


class TestGetOrder:
    def test_gets_existing_order(self, uow, bus):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order = create_uc.execute("Juan", SAMPLE_ITEMS)

        get_uc = GetOrderUseCase(uow=uow)
        found = get_uc.execute(order.id)

        assert found.customer == "Juan"

    def test_not_found_raises(self, uow, bus):
        uc = GetOrderUseCase(uow=uow)
        with pytest.raises(OrderNotFoundError):
            uc.execute(999)


class TestListOrders:
    def test_list_all(self, uow, bus):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        create_uc.execute("Juan", SAMPLE_ITEMS)
        create_uc.execute("María", SAMPLE_ITEMS)

        list_uc = ListOrdersUseCase(uow=uow)
        orders = list_uc.execute()

        assert len(orders) == 2

    def test_filter_by_status(self, uow, bus):
        create_uc = CreateOrderUseCase(uow=uow, publisher=bus)
        order1 = create_uc.execute("Juan", SAMPLE_ITEMS)
        create_uc.execute("María", SAMPLE_ITEMS)

        complete_uc = CompleteOrderUseCase(uow=uow, publisher=bus)
        complete_uc.execute(order1.id)

        list_uc = ListOrdersUseCase(uow=uow)
        completed = list_uc.execute(status="completed")
        pending = list_uc.execute(status="pending")

        assert len(completed) == 1
        assert len(pending) == 1
        assert completed[0].customer == "Juan"
