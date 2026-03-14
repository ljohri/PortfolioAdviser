from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.api.main import create_app
from app.config import Settings, get_settings
from app.db.engine import get_db_session
from app.db.models import Base


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
def db_session(db_engine) -> Generator[Session, None, None]:
    testing_session_factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    session = testing_session_factory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture()
def test_settings() -> Settings:
    return Settings(
        database_url=_integration_database_url(),
        tiingo_api_token="test-token",
        tiingo_base_url="https://api.tiingo.test",
        app_env="test",
    )


@pytest.fixture()
def client(db_session: Session, test_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db_session():
        yield db_session

    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
