import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        logger.info(
            "[%s] %s %s — inicio",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start

            logger.info(
                "[%s] %s %s — %d — %.3fs",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
            return response

        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.exception(
                "[%s] %s %s — error — %.3fs — %s",
                request_id,
                request.method,
                request.url.path,
                elapsed,
                e,
            )
            raise
