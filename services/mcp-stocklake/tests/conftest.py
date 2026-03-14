from __future__ import annotations

import os
import sys
from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from mcp_stocklake.datalake_runtime import bootstrap_datalake_path
from mcp_stocklake.datalake_service import ServiceDependencies
from mcp_stocklake.tools import StocklakeTools

bootstrap_datalake_path()

from app.config import Settings  # noqa: E402
from app.db.models import Base  # noqa: E402


def _integration_database_url() -> str:
    return os.getenv(
        "INTEGRATION_DATABASE_URL",
        "postgresql+psycopg://stocklake:stocklake@localhost:5432/stocklake",
    )


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(_integration_database_url(), future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"Docker Postgres is not reachable for integration tests: {exc}")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session_factory(db_engine) -> sessionmaker[Session]:
    return sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def db_session(db_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = db_session_factory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture()
def service_dependencies(db_session_factory: sessionmaker[Session]) -> ServiceDependencies:
    settings = Settings(
        database_url=_integration_database_url(),
        tiingo_api_token="test-token",
        tiingo_base_url="https://api.tiingo.test",
        app_env="test",
    )
    return ServiceDependencies(
        settings=settings,
        session_factory=db_session_factory,
    )


@pytest.fixture()
def stocklake_tools(service_dependencies: ServiceDependencies) -> StocklakeTools:
    return StocklakeTools.from_dependencies(service_dependencies)


@pytest.fixture()
def tiingo_payload_factory():
    def _payload(*, trading_date: date, close: float = 105.0) -> dict:
        return {
            "date": f"{trading_date.isoformat()}T00:00:00.000Z",
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": close,
            "volume": 1_000_000,
            "adjOpen": 99.0,
            "adjHigh": 109.0,
            "adjLow": 94.0,
            "adjClose": close - 1.0,
            "adjVolume": 1_100_000,
            "adjFactor": 1.0,
            "divCash": 0.0,
            "splitFactor": 1.0,
        }

    return _payload

