import logging

from sqlalchemy.orm import Session

from alembic.environment import Any
from src.infrastructure.adapters.database import SessionFactory, create_tables
from src.infrastructure.adapters.sql_models import OrderItemModel, OrderModel, UserModel

logger = logging.getLogger(__name__)

SEED_USERS: list[dict[str, str]] = [
    {"name": "Juan Pérez", "email": "juan@example.com"},
    {"name": "María García", "email": "maria@example.com"},
    {"name": "Ana López", "email": "ana@example.com"},
    {"name": "Pedro Ramírez", "email": "pedro@example.com"},
]

SEED_ORDERS: list[dict[str, Any]] = [
    {
        "customer": "Juan Pérez",
        "status": "completed",
        "items": [
            {"product": "Laptop HP", "price": 25000, "quantity": 1},
            {"product": "Mouse Logitech", "price": 350, "quantity": 2},
        ],
    },
    {
        "customer": "Juan Pérez",
        "status": "pending",
        "items": [
            {"product": "Monitor Samsung 27''", "price": 8500, "quantity": 1},
        ],
    },
    {
        "customer": "María García",
        "status": "completed",
        "items": [
            {"product": "Teclado mecánico", "price": 1800, "quantity": 1},
            {"product": "Webcam HD", "price": 1200, "quantity": 1},
            {"product": "Audífonos Sony", "price": 2500, "quantity": 1},
        ],
    },
    {
        "customer": "María García",
        "status": "cancelled",
        "items": [
            {"product": "iPad Air", "price": 15000, "quantity": 1},
        ],
    },
    {
        "customer": "Ana López",
        "status": "pending",
        "items": [
            {"product": "Cable USB-C", "price": 150, "quantity": 5},
            {"product": "Hub USB", "price": 800, "quantity": 1},
        ],
    },
    {
        "customer": "Pedro Ramírez",
        "status": "completed",
        "items": [
            {"product": "SSD 1TB", "price": 2200, "quantity": 2},
            {"product": "RAM 16GB", "price": 1500, "quantity": 2},
            {"product": "Gabinete ATX", "price": 1800, "quantity": 1},
        ],
    },
]


def seed_database() -> None:
    """Inserta datos de prueba si la base está vacía."""
    create_tables()
    session: Session = SessionFactory()

    try:
        existing_users = session.query(UserModel).count()
        if existing_users > 0:
            logger.info("Base de datos ya tiene datos — seed omitido")
            return

        # Crear usuarios
        users: dict[str, UserModel] = {}
        for data in SEED_ORDERS:
            user = users[data["customer"]]
            order = OrderModel(
                user=user,
                status=data["status"],
                items=[
                    OrderItemModel(
                        product=item["product"],
                        price=item["price"],
                        quantity=item["quantity"],
                    )
                    for item in data["items"]
                ],
            )
            session.add(order)
        # Crear órdenes
        for data in SEED_ORDERS:
            user = users[data["customer"]]
            order = OrderModel(
                user=user,
                status=data["status"],
                items=[OrderItemModel(**item) for item in data["items"]],
            )
            session.add(order)

        session.commit()
        logger.info(
            "Seed completado: %d usuarios, %d órdenes",
            len(SEED_USERS),
            len(SEED_ORDERS),
        )

    except Exception:
        session.rollback()
        logger.exception("Error al hacer seed")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    seed_database()
