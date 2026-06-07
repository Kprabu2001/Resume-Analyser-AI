import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable, List

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.base.base import ApiResponse

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class AppServer(FastAPI):
    """
    FastAPI subclass with:
      - Request ID generation / propagation (X-Request-ID header)
      - Request duration tracking and logging
      - Consistent error responses
    """

    def __init__(self, lifespan_handlers: List[Callable] = None, **kwargs):
        # kwargs.pop("lifespan",None)
        # combined_lifespan = self._create_combined_lifespan(lifespan_handlers or [])
        user_lifespan = kwargs.pop("lifespan", None)
        handlers = (lifespan_handlers or []) + ([user_lifespan] if user_lifespan else [])
        combined_lifespan = self._create_combined_lifespan(handlers)
        super().__init__(lifespan=combined_lifespan, **kwargs, redirect_slashes=False)
        self.middleware("http")(self._request_middleware)

    def _create_combined_lifespan(self, handlers: List[Callable]):
        @asynccontextmanager
        async def combined_lifespan(app: FastAPI):
            contexts = []
            for handler in handlers:
                ctx = handler(app)
                await ctx.__aenter__()
                contexts.append(ctx)
            try:
                yield
            finally:
                for ctx in reversed(contexts):
                    await ctx.__aexit__(None, None, None)

        return combined_lifespan

    async def _request_middleware(self, request: Request, call_next):
        start_time = time.perf_counter()
        status_code = 500

        request_id = request.headers.get(REQUEST_ID_HEADER, f"API-{uuid.uuid4()}")

        logger.info(
            f"{request.method} {request.url.path} - Request started",
            extra={"request_id": request_id, "http_method": request.method, "http_path": request.url.path},
        )

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(
                f"{request.method} {request.url.path} - Handler error: {e}",
                exc_info=True,
                extra={"request_id": request_id},
            )
            return self._error_response(500, "Internal Server Error", request_id)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                f"{request.method} {request.url.path} - {status_code} in {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "httpRequest": {
                        "requestMethod": request.method,
                        "requestUrl": str(request.url),
                        "status": status_code,
                        "latency": f"{duration_ms}ms",
                    },
                },
            )

    def _error_response(self, status_code: int, message: str, request_id: str) -> JSONResponse:
        response = JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(ApiResponse(message=message), exclude_none=True),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
