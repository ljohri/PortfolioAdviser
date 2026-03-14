from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse

from app.adapters.current_market import CurrentMarketAdapter
from app.adapters.datalake import DatalakeAdapter
from app.config import Settings, get_settings
from app.duckdb_connect import get_duckdb_connection
from app.mcp_tools import ScreenerMcpTools
from app.models import PresetDefinition, ScreenRequest, ScreenResponse, ValidateRequest, ValidationResponse
from app.presets import get_presets
from app.services.engine import ScreenerEngine


@dataclass
class ServiceContainer:
    engine: ScreenerEngine
    mcp_tools: ScreenerMcpTools


def _build_services(settings: Settings) -> ServiceContainer:
    connection = get_duckdb_connection()
    datalake = DatalakeAdapter(connection)
    current_market = CurrentMarketAdapter(timeout_seconds=settings.market_live_timeout_seconds)
    engine = ScreenerEngine(datalake_adapter=datalake, current_market_adapter=current_market)
    return ServiceContainer(engine=engine, mcp_tools=ScreenerMcpTools(engine=engine))


def create_app() -> FastAPI:
    app = FastAPI(title="stocklake-screener", default_response_class=ORJSONResponse)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/screen/validate", response_model=ValidationResponse)
    def validate_screen(payload: ValidateRequest, settings: Settings = Depends(get_settings)) -> ValidationResponse:
        services = _build_services(settings)
        request = ScreenRequest(
            symbols=[],
            source={"mode": "canonical_tables", "postgres_dsn": settings.datalake_postgres_dsn},
            start_date=payload.start_date,
            end_date=payload.end_date,
            rules=payload.rules,
        )
        return services.engine.validate_criteria(request)

    @app.post("/screen/run", response_model=ScreenResponse)
    def run_screen(payload: ScreenRequest, settings: Settings = Depends(get_settings)) -> ScreenResponse:
        services = _build_services(settings)
        request_payload = payload.model_dump(mode="json", by_alias=True)
        source = request_payload["source"]
        if source.get("mode") == "canonical_tables" and not source.get("postgres_dsn"):
            source["postgres_dsn"] = settings.datalake_postgres_dsn
        request_payload["source"] = source
        request = ScreenRequest.model_validate(request_payload)
        return services.engine.run(request)

    @app.get("/screen/presets", response_model=list[PresetDefinition])
    def list_presets() -> list[PresetDefinition]:
        return get_presets()

    return app


app = create_app()
