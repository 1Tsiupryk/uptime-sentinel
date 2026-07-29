from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ready_check(monkeypatch):
    monkeypatch.setattr(
        "app.api.health.check_database_connection",
        lambda: True,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_ready_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.api.health.check_database_connection",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database connection error."
    }