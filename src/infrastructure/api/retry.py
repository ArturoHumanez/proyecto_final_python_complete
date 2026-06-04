import functools
import logging
import time

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorador de reintentos con backoff exponencial."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            "%s falló después de %d intentos: %s",
                            func.__name__,
                            max_attempts,
                            e,
                        )
                        raise
                    logger.warning(
                        "%s intento %d/%d falló: %s — reintentando en %.1fs",
                        func.__name__,
                        attempt,
                        max_attempts,
                        e,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper

    return decorator
