class DomainError(Exception):
    """Base para errores de dominio."""


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: int) -> None:
        self.order_id = order_id
        super().__init__(f"Orden {order_id} no encontrada")


class InvalidOrderError(DomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Orden inválida: {reason}")


class OrderStateError(DomainError):
    def __init__(self, order_id: int | None, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Orden {order_id}: no se puede pasar de '{current}' a '{target}'"
        )
