import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.base.base import ApiResponse
from app.base.constants import ACCESS_COOKIE
from app.base.log_context import init_log_context, clear_log_context
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

PUBLIC_PATHS = frozenset({
    "/health", "/",
    "/docs", "/openapi.json", "/redoc",
    "/auth/signup", "/auth/login", "/auth/refresh",
})


class AppServer(FastAPI):
    """
    FastAPI subclass with:
      - Request ID generation / propagation (X-Request-ID header)
      - Request duration tracking and logging
      - Consistent error responses
      - JWT authentication for protected paths (sets request.state.user_id)
    """

    def __init__(self, lifespan_handlers: List[Callable] = None, **kwargs):
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
        init_log_context(request_id)

        logger.info(f"{request.method} {request.url.path} - Request started")

        # ── Authentication (before routing) ─────────────────────────────
        if not self._is_public_path(request.url.path):
            auth_response = await self._authenticate(request, request_id)
            if auth_response:
                return auth_response

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(f"{request.method} {request.url.path} - Handler error: {e}", exc_info=True)
            return self._error_response(500, "Internal Server Error", request_id)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(f"{request.method} {request.url.path} - {status_code} in {duration_ms}ms")
            clear_log_context()

    def _is_public_path(self, path: str) -> bool:
        if path in PUBLIC_PATHS:
            return True
        if path.startswith(("/auth/", "/docs", "/openapi.json", "/redoc")):
            return True
        return False

    async def _authenticate(self, request: Request, request_id: str) -> JSONResponse | None:
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get(ACCESS_COOKIE)

        if not token:
            return self._error_response(401, "Not authenticated", request_id)

        try:
            payload = TokenService.verify_token(token)
        except HTTPException:
            return self._error_response(401, "Invalid or expired token", request_id)

        if payload.get("token_type") != "access":
            return self._error_response(401, "Invalid token type", request_id)

        request.state.user_id = payload.get("user_id")
        return None

    def _error_response(self, status_code: int, message: str, request_id: str) -> JSONResponse:
        response = JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(ApiResponse(message=message), exclude_none=True),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
