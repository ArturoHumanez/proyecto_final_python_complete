from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    order_id: int = 0
    customer: str = ""
    total: float = 0.0


@dataclass(frozen=True)
class OrderCompleted(DomainEvent):
    order_id: int = 0
    customer: str = ""


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: int = 0
    customer: str = ""
    reason: str = ""
