from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.errors import register_exception_handlers
from app.routes.health import router as health_router
from app.routes.v1 import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="stocklake-api-gateway",
        default_response_class=ORJSONResponse,
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(v1_router)
    return app


app = create_app()
