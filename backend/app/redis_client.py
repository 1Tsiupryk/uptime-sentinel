import logging

from redis import Redis
from redis.exceptions import RedisError

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

def create_redis_client(settings: Settings | None = None) -> Redis:

    current_settings = settings or get_settings()

    return Redis(
        host=current_settings.REDIS_HOST,
        port=current_settings.REDIS_PORT,
        db=current_settings.REDIS_DB,
        socket_connect_timeout=current_settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        socket_timeout=current_settings.REDIS_SOCKET_TIMEOUT_SECONDS
    )


def check_redis_connection(client: Redis) -> bool:
    try:
        return client.ping()
    except RedisError as exc:
        logger.exception("Redis connection check failed: %s", exc)
        return False