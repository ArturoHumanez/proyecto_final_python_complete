import logging

from src.application.event_handlers import EventBus
from src.domain.events import OrderCancelled, OrderCompleted, OrderCreated

logger = logging.getLogger(__name__)


def on_order_created(event: OrderCreated) -> None:
    logger.info(
        "Orden #%d creada — cliente: %s, total: $%.2f",
        event.order_id,
        event.customer,
        event.total,
    )


def on_order_completed(event: OrderCompleted) -> None:
    logger.info(
        "Orden #%d completada — cliente: %s",
        event.order_id,
        event.customer,
    )


def on_order_cancelled(event: OrderCancelled) -> None:
    logger.info(
        "Orden #%d cancelada — cliente: %s, motivo: %s",
        event.order_id,
        event.customer,
        event.reason or "sin motivo",
    )


def register_all(bus: "EventBus") -> None:

    bus.register(OrderCreated, on_order_created)
    bus.register(OrderCompleted, on_order_completed)
    bus.register(OrderCancelled, on_order_cancelled)
