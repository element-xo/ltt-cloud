import json
import hashlib

import redis

from .config import get_settings


def _get_redis_client() -> redis.Redis:
    """Create a Redis client from the current settings.

    The REDIS_URL env var provides the full connection string.
    """
    settings = get_settings()
    return redis.Redis.from_url(settings.REDIS_URL)


def make_lca_key(functional_unit: dict, method: tuple) -> str:
    data = json.dumps({"fu": functional_unit, "method": method}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def get_cached_lca(key: str) -> dict | None:
    client = _get_redis_client()
    data = client.get(key)
    return json.loads(data) if data else None


def set_cached_lca(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    client = _get_redis_client()
    client.setex(key, ttl_seconds, json.dumps(value))