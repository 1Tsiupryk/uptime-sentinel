from fastapi.testclient import TestClient

def test_create_monitor(client: TestClient) -> None:
    response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Example Website"
    assert data["url"] == "https://example.com/"
    assert data["interval_seconds"] == 60
    assert data["timeout_seconds"] == 5
    assert data["expected_status_code"] == 200
    assert data["enabled"] is True
    assert isinstance(data["id"], int)
    assert data["created_at"] is not None


def test_list_monitors(client: TestClient) -> None:
    create_response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )
    assert create_response.status_code == 201

    response = client.get("/monitors")

    assert response.status_code == 200

    monitors = response.json()

    assert len(monitors) == 1
    assert monitors[0]["name"] == "Example Website"

def test_get_monitor(client: TestClient) -> None:
    create_response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )
    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]
    response = client.get(f"/monitors/{monitor_id}")

    assert response.status_code == 200
    assert response.json()["id"] == monitor_id
    assert response.json()["name"] == "Example Website"

def test_update_monitor(client: TestClient) -> None:
    create_response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )
    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]
    response = client.patch(f"/monitors/{monitor_id}", json={"interval_seconds": 120})

    assert response.status_code == 200
    assert response.json()["id"] == monitor_id
    assert response.json()["interval_seconds"] == 120

def test_delete_monitor(client: TestClient) -> None:
    create_response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )
    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]
    response = client.delete(f"/monitors/{monitor_id}")

    assert response.status_code == 204

def test_get_missing_monitor_returns_404(client: TestClient) -> None:
    response = client.get("/monitors/999")

    assert response.status_code == 404

def test_update_missing_monitor_returns_404(client: TestClient) -> None:
    response = client.patch("/monitors/999", json={"name": "Updated Website"})

    assert response.status_code == 404

def test_delete_missing_monitor_returns_404(client: TestClient) -> None:
    response = client.delete("/monitors/999")

    assert response.status_code == 404

def test_invalid_monitor_returns_422(client: TestClient) -> None:
    response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "invalid-url",
        },
    )

    assert response.status_code == 422

def test_update_invalid_monitor_returns_422(client: TestClient) -> None:
    create_response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )
    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]
    response = client.patch(f"/monitors/{monitor_id}", json={"url": "invalid-url"})

    assert response.status_code == 422

