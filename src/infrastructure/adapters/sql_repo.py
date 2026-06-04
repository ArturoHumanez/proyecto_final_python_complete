from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities import Order, OrderItem
from src.infrastructure.adapters.sql_models import OrderItemModel, OrderModel, UserModel


class SqlOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, model: OrderModel) -> Order:
        """Convierte un modelo SQLAlchemy a entidad de dominio."""
        return Order(
            id=model.id,
            customer=model.user.name,
            status=model.status,
            created_at=model.created_at,
            items=[
                OrderItem(
                    product=item.product,
                    price=item.price,
                    quantity=item.quantity,
                )
                for item in model.items
            ],
        )

    def _get_or_create_user(self, customer: str) -> UserModel:
        """Busca un usuario por nombre o lo crea."""
        stmt = select(UserModel).where(UserModel.name == customer)
        user = self._session.scalars(stmt).first()
        if not user:
            user = UserModel(
                name=customer,
                email=f"{customer.lower().replace(' ', '.')}@example.com",
            )
            self._session.add(user)
            self._session.flush()
        return user

    def save(self, order: Order) -> Order:
        if order.id:
            model = self._session.get(OrderModel, order.id)
            if model:
                model.status = order.status
                self._session.flush()
                return self._to_domain(model)

        user = self._get_or_create_user(order.customer)
        model = OrderModel(
            user=user,
            status=order.status,
            created_at=order.created_at,
            items=[
                OrderItemModel(
                    product=item.product,
                    price=item.price,
                    quantity=item.quantity,
                )
                for item in order.items
            ],
        )
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def find_by_id(self, order_id: int) -> Order | None:
        model = self._session.get(OrderModel, order_id)
        if not model:
            return None
        return self._to_domain(model)

    def find_all(self) -> list[Order]:
        stmt = select(OrderModel)
        models = list(self._session.scalars(stmt))
        return [self._to_domain(m) for m in models]

    def find_by_status(self, status: str) -> list[Order]:
        stmt = select(OrderModel).where(OrderModel.status == status)
        models = list(self._session.scalars(stmt))
        return [self._to_domain(m) for m in models]

    def delete(self, order_id: int) -> bool:
        model = self._session.get(OrderModel, order_id)
        if not model:
            return False
        self._session.delete(model)
        self._session.flush()
        return True
