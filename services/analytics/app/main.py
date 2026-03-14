from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, FastAPI, HTTPException

from app.adapters.current_market import CurrentMarketAdapter
from app.adapters.datalake import DatalakeAdapter
from app.config import Settings, get_settings
from app.duckdb_connect import get_duckdb_connection
from app.models import AnalyzeRequest, AnalyzeResponse, PortfolioReport, UniverseRequest, UniverseResponse
from app.services.jobs import InMemoryJobStore
from app.services.portfolio_analytics import PortfolioAnalyticsService

JOB_STORE = InMemoryJobStore()


@dataclass
class ServiceContainer:
    portfolio_analytics: PortfolioAnalyticsService
    current_market: CurrentMarketAdapter


def _build_services(settings: Settings) -> ServiceContainer:
    connection = get_duckdb_connection()
    adapter = DatalakeAdapter(connection)
    portfolio_analytics = PortfolioAnalyticsService(
        adapter=adapter,
        artifacts_dir=settings.artifacts_dir,
    )
    current_market = CurrentMarketAdapter()
    return ServiceContainer(portfolio_analytics=portfolio_analytics, current_market=current_market)


def create_app() -> FastAPI:
    app = FastAPI(title="stocklake-analytics")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/portfolio/universe", response_model=UniverseResponse)
    def create_portfolio_universe(
        payload: UniverseRequest,
        settings: Settings = Depends(get_settings),
    ) -> UniverseResponse:
        services = _build_services(settings)
        source = payload.source.model_dump(by_alias=True)
        if source.get("mode") == "canonical_tables" and not source.get("postgres_dsn"):
            source["postgres_dsn"] = settings.datalake_postgres_dsn
        normalized_symbols = services.portfolio_analytics.normalize_universe(
            symbols=payload.symbols,
            source=source,
        )
        if not normalized_symbols:
            raise HTTPException(status_code=400, detail="No valid active symbols found in source")
        job = JOB_STORE.create_universe_job(symbols=normalized_symbols, source=source)
        return UniverseResponse(
            job_id=job.job_id,
            normalized_symbols=normalized_symbols,
            source_mode=source["mode"],
        )

    @app.post("/portfolio/analyze", response_model=AnalyzeResponse)
    def analyze_portfolio(
        payload: AnalyzeRequest,
        settings: Settings = Depends(get_settings),
    ) -> AnalyzeResponse:
        services = _build_services(settings)
        job = JOB_STORE.get_job(payload.job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Unknown job_id: {payload.job_id}")
        if payload.start_date > payload.end_date:
            raise HTTPException(status_code=422, detail="start_date must be <= end_date")
        current_prices = {symbol.upper(): float(price) for symbol, price in payload.current_prices.items()}
        if payload.data_mode in {"current", "blended"}:
            base_url = payload.current_api_base_url or settings.market_live_base_url
            missing_symbols = [symbol for symbol in job.symbols if symbol not in current_prices]
            if missing_symbols:
                fetched = services.current_market.get_current_prices(
                    symbols=missing_symbols,
                    base_url=base_url,
                )
                current_prices.update(fetched)
            if payload.data_mode == "current" and not current_prices:
                raise HTTPException(
                    status_code=422,
                    detail="current mode requires current_prices or reachable current API data",
                )
        report = services.portfolio_analytics.analyze(
            job_id=job.job_id,
            symbols=job.symbols,
            source=job.source,
            start_date=payload.start_date,
            end_date=payload.end_date,
            rolling_window_days=payload.rolling_window_days,
            top_n=payload.top_n,
            data_mode=payload.data_mode,
            current_prices=current_prices,
            export_parquet=payload.export_parquet,
        )
        JOB_STORE.save_report(job_id=job.job_id, report=report)
        return AnalyzeResponse(
            job_id=job.job_id,
            report_ready=True,
            analysis_mode=report.analysis_mode,
            source_mode=report.source_mode,
            data_sources_used=report.data_sources_used,
            current_prices_used=report.current_prices_used,
            symbols_analyzed=len(report.ranking),
            rows_in_portfolio_input=len(report.portfolio_input_rows),
            parquet_path=report.parquet_path,
        )

    @app.get("/portfolio/report/{job_id}", response_model=PortfolioReport)
    def get_portfolio_report(job_id: str) -> PortfolioReport:
        job = JOB_STORE.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Unknown job_id: {job_id}")
        if job.report is None:
            raise HTTPException(status_code=404, detail=f"Report not ready for job_id: {job_id}")
        return job.report

    return app


app = create_app()
