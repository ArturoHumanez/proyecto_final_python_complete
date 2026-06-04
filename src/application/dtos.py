from pydantic import BaseModel, Field


class OrderItemDTO(BaseModel):
    product: str
    price: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)


class CreateOrderDTO(BaseModel):
    customer: str = Field(min_length=1)
    items: list[OrderItemDTO] = Field(min_length=1)


class UpdateOrderStatusDTO(BaseModel):
    status: str = Field(pattern="^(completed|cancelled)$")
    reason: str = ""


class OrderItemResponse(BaseModel):
    product: str
    price: float
    quantity: int
    subtotal: float


class OrderResponse(BaseModel):
    id: int
    customer: str
    status: str
    total: float
    item_count: int
    created_at: str
    items: list[OrderItemResponse]
