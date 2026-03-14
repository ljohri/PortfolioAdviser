from fastapi.testclient import TestClient

from app.api.main import create_app


def test_market_live_health_smoke() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
