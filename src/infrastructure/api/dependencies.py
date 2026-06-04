from typing import Any

from src.application.event_handlers import EventBus
from src.application.handlers.order_handlers import register_all
from src.application.use_cases import (
    CancelOrderUseCase,
    CompleteOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from src.infrastructure.adapters.sql_uow import SqlUnitOfWork

_event_bus = EventBus()
register_all(_event_bus)


def _uow() -> Any:
    return SqlUnitOfWork()


def get_create_order_uc() -> CreateOrderUseCase:
    return CreateOrderUseCase(uow=_uow(), publisher=_event_bus)


def get_complete_order_uc() -> CompleteOrderUseCase:
    return CompleteOrderUseCase(uow=_uow(), publisher=_event_bus)


def get_cancel_order_uc() -> CancelOrderUseCase:
    return CancelOrderUseCase(uow=_uow(), publisher=_event_bus)


def get_get_order_uc() -> GetOrderUseCase:
    return GetOrderUseCase(uow=_uow())


def get_list_orders_uc() -> ListOrdersUseCase:
    return ListOrdersUseCase(uow=_uow())
