from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import ORJSONResponse

from app.config import Settings, get_settings
from app.models import CurrentBarResponse
from app.services.current_service import CurrentService
from app.services.tiingo_client import TiingoClient


def _build_current_service(settings: Settings) -> CurrentService:
    return CurrentService(tiingo_client=TiingoClient(settings))


def create_app() -> FastAPI:
    app = FastAPI(
        title="stocklake-market-live",
        default_response_class=ORJSONResponse,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/current/{symbol}", response_model=CurrentBarResponse)
    async def get_current(
        symbol: str,
        settings: Settings = Depends(get_settings),
    ) -> CurrentBarResponse:
        service = _build_current_service(settings)
        bar = await service.get_current_bar(symbol)
        if bar is None:
            raise HTTPException(status_code=404, detail=f"no current bar found for {symbol.upper()}")
        return bar

    return app


app = create_app()
