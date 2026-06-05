from fastapi import APIRouter, Depends, HTTPException

from src.application.dtos import (
    CreateOrderDTO,
    OrderItemResponse,
    OrderResponse,
    UpdateOrderStatusDTO,
)
from src.application.use_cases import (
    CancelOrderUseCase,
    CompleteOrderUseCase,
    CreateOrderUseCase,
    DeleteOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from src.domain.entities import Order
from src.domain.exceptions import OrderNotFoundError, OrderStateError
from src.infrastructure.api.auth import get_current_user
from src.infrastructure.api.dependencies import (
    get_cancel_order_uc,
    get_complete_order_uc,
    get_create_order_uc,
    get_delete_order_uc,
    get_get_order_uc,
    get_list_orders_uc,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id or 0,
        customer=order.customer,
        status=order.status,
        total=order.total,
        item_count=order.item_count,
        created_at=order.created_at.isoformat(),
        items=[
            OrderItemResponse(
                product=i.product,
                price=i.price,
                quantity=i.quantity,
                subtotal=i.subtotal,
            )
            for i in order.items
        ],
    )


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    data: CreateOrderDTO,
    uc: CreateOrderUseCase = Depends(get_create_order_uc),
    user: dict = Depends(get_current_user),
):
    items = [item.model_dump() for item in data.items]
    order = uc.execute(data.customer, items)
    return _to_response(order)


@router.get("/", response_model=list[OrderResponse])
def list_orders(
    status: str | None = None,
    uc: ListOrdersUseCase = Depends(get_list_orders_uc),
):
    orders = uc.execute(status)
    return [_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    uc: GetOrderUseCase = Depends(get_get_order_uc),
):
    try:
        order = uc.execute(order_id)
        return _to_response(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Orden no encontrada")


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: UpdateOrderStatusDTO,
    complete_uc: CompleteOrderUseCase = Depends(get_complete_order_uc),
    cancel_uc: CancelOrderUseCase = Depends(get_cancel_order_uc),
    user: dict = Depends(get_current_user),
):
    try:
        if data.status == "completed":
            order = complete_uc.execute(order_id)
        else:
            order = cancel_uc.execute(order_id, reason=data.reason)
        return _to_response(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    except OrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    uc: DeleteOrderUseCase = Depends(get_delete_order_uc),
    user: dict = Depends(get_current_user),
):
    try:
        uc.execute(order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
