from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.models import ErrorBody, ErrorResponse


class GatewayError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class UpstreamHttpError(Exception):
    def __init__(self, *, status_code: int, detail: str | None = None) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail or f"upstream HTTP {status_code}")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(GatewayError)
    async def handle_gateway_error(_: Request, exc: GatewayError) -> ORJSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(code=exc.code, message=exc.message, details=exc.details),
        )
        return ORJSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))
