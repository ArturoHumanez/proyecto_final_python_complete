from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(200), default=None)

    orders: Mapped[list["OrderModel"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"UserModel(id={self.id}, name='{self.name}')"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["UserModel"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"OrderModel(id={self.id}, status='{self.status}')"


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product: Mapped[str] = mapped_column(String(200))
    price: Mapped[float]
    quantity: Mapped[int] = mapped_column(default=1)

    order: Mapped["OrderModel"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"OrderItemModel('{self.product}', ${self.price}x{self.quantity})"
