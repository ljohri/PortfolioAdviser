from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from mcp_stocklake.datalake_runtime import bootstrap_datalake_path

bootstrap_datalake_path()

from app.config import Settings, get_settings  # noqa: E402
from app.db.engine import get_session_factory  # noqa: E402
from app.repositories.bars import BarRepository  # noqa: E402
from app.repositories.tickers import TickerRepository  # noqa: E402
from app.services.backfill_service import BackfillService  # noqa: E402
from app.services.bar_ingestion_service import BarIngestionService  # noqa: E402
from app.services.impl.backfill_logic import BackfillServiceImpl  # noqa: E402
from app.services.impl.bar_ingestion_logic import BarIngestionServiceImpl  # noqa: E402
from app.services.impl.stocklake_logic import StocklakeServiceImpl  # noqa: E402
from app.services.impl.ticker_logic import TickerServiceImpl  # noqa: E402
from app.services.stocklake_service import StocklakeService  # noqa: E402
from app.services.ticker_service import TickerService  # noqa: E402
from app.services.tiingo_client import TiingoClient  # noqa: E402


@dataclass(frozen=True)
class ServiceDependencies:
    """Dependency bundle used to construct stocklake service instances."""

    settings: Settings
    session_factory: sessionmaker[Session]


@dataclass(frozen=True)
class StocklakeRuntime:
    """Runtime object with stocklake service and live DB session."""

    service: StocklakeService
    session: Session


def default_dependencies() -> ServiceDependencies:
    """
    Build stocklake dependencies from datalake runtime configuration.

    Returns:
        Dependencies configured from datalake environment settings.
    """
    return ServiceDependencies(
        settings=get_settings(),
        session_factory=get_session_factory(),
    )


def create_stocklake_runtime(deps: ServiceDependencies) -> StocklakeRuntime:
    """
    Create a stocklake service bound to a fresh SQLAlchemy session.

    Args:
        deps: Runtime dependencies with settings and session factory.

    Returns:
        A runtime with fully wired service and its active session.
    """
    session = deps.session_factory()
    ticker_repository = TickerRepository(session)
    bar_repository = BarRepository(session)
    tiingo_client = TiingoClient(deps.settings)
    ticker_service = TickerService(TickerServiceImpl(ticker_repository=ticker_repository))
    bar_ingestion_service = BarIngestionService(BarIngestionServiceImpl(bar_repository=bar_repository))
    backfill_service = BackfillService(
        BackfillServiceImpl(
            session=session,
            ticker_repository=ticker_repository,
            tiingo_client=tiingo_client,
            bar_ingestion_service=bar_ingestion_service,
        )
    )
    service = StocklakeService(
        StocklakeServiceImpl(
            ticker_service=ticker_service,
            ticker_repository=ticker_repository,
            bar_repository=bar_repository,
            backfill_service=backfill_service,
        )
    )
    return StocklakeRuntime(service=service, session=session)
