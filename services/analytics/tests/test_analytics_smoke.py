from __future__ import annotations

from app.main import create_app


def test_analytics_service_smoke() -> None:
    app = create_app()
    assert app.title == "stocklake-analytics"
