import logging

from src.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list] = {}

    def register(self, event_type: type, handler: object) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            handlers = self._handlers.get(type(event), [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception:
                    logger.exception("Error al manejar evento %s", type(event).__name__)
