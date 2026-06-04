from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.events import DomainEvent, OrderCancelled, OrderCompleted, OrderCreated
from src.domain.exceptions import InvalidOrderError, OrderStateError


@dataclass
class OrderItem:
    product: str
    price: float
    quantity: int = 1

    @property
    def subtotal(self) -> float:
        return self.price * self.quantity

    def __post_init__(self) -> None:
        if not self.product.strip():
            raise InvalidOrderError("El producto no puede estar vacío")
        if self.price <= 0:
            raise InvalidOrderError(f"Precio debe ser positivo, recibido: {self.price}")
        if self.quantity < 1:
            raise InvalidOrderError(
                f"Cantidad debe ser >= 1, recibido: {self.quantity}"
            )


VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


@dataclass
class Order:
    customer: str
    items: list[OrderItem]
    id: int | None = None
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def _transition_to(self, target: str) -> None:  # DRY
        """Valida y ejecuta una transición de estado."""
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if target not in allowed:
            raise OrderStateError(self.id, self.status, target)
        self.status = target

    def mark_created(self) -> None:
        self.events.append(
            OrderCreated(
                order_id=self.id or 0,
                customer=self.customer,
                total=self.total,
            )
        )

    def complete(self) -> None:
        self._transition_to("completed")
        self.events.append(
            OrderCompleted(order_id=self.id or 0, customer=self.customer)
        )

    def cancel(self, reason: str = "") -> None:
        self._transition_to("cancelled")
        self.events.append(
            OrderCancelled(
                order_id=self.id or 0,
                customer=self.customer,
                reason=reason,
            )
        )

    def collect_events(self) -> list[DomainEvent]:
        events = self.events.copy()
        self.events.clear()
        return events

    def __post_init__(self) -> None:
        if not self.customer.strip():
            raise InvalidOrderError("Customer no puede estar vacío")
        if not self.items:
            raise InvalidOrderError("La orden debe tener al menos un item")
        if self.status not in VALID_TRANSITIONS:
            raise InvalidOrderError(f"Status inválido: {self.status}")
