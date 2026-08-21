from unittest.mock import Mock

import pytest
from redis.exceptions import RedisError

from app.config import Settings
from app.redis_client import (
    check_redis_connection,
    create_redis_client,
)

def make_settings() -> Settings:
    return Settings(
        PROJECT_NAME="Uptime Sentinel",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_USER="sentinel",
        POSTGRES_PASSWORD="secret",
        POSTGRES_DB="sentinel",
        REDIS_HOST="redis",
        REDIS_PORT=6379,
        REDIS_DB=0,
        REDIS_SOCKET_TIMEOUT_SECONDS=2,
    )

def test_create_redis_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_redis_class = Mock()
    monkeypatch.setattr(
        "app.redis_client.Redis",
        mock_redis_class,
    )

    client = create_redis_client(make_settings())

    assert client is mock_redis_class.return_value

    mock_redis_class.assert_called_once_with(
        host="redis",
        port=6379,
        db=0,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

def test_check_redis_connection_returns_true() -> None:
    client = Mock()
    client.ping.return_value = True

    assert check_redis_connection(client) is True
    client.ping.assert_called_once()

def test_check_redis_connection_returns_false_on_error(
    caplog: pytest.LogCaptureFixture
) -> None:
    client = Mock()
    client.ping.side_effect = RedisError("Connection refused")

    assert check_redis_connection(client) is False
    assert "Redis connection check failed" in caplog.text
    assert "Connection refused" in caplog.text

