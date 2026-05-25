"""缓存服务：Redis 优先，异常时静默降级。"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import redis

from app.config import settings


_client: redis.Redis | None = None


def get_cache_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def make_cache_key(namespace: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"name:{namespace}:{digest}"


def get_json(key: str) -> Any | None:
    try:
        raw = get_cache_client().get(key)
    except redis.RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_json(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    try:
        get_cache_client().setex(
            key,
            ttl_seconds,
            json.dumps(value, ensure_ascii=False, sort_keys=True),
        )
    except redis.RedisError:
        return
