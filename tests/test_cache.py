import redis

from app.services import cache


def test_make_cache_key_is_stable_for_sorted_payload():
    first = cache.make_cache_key("generate", {"b": 2, "a": 1})
    second = cache.make_cache_key("generate", {"a": 1, "b": 2})

    assert first == second
    assert first.startswith("name:generate:")


def test_get_json_returns_none_when_redis_unavailable(monkeypatch):
    class BrokenClient:
        def get(self, key):
            raise redis.RedisError("down")

    monkeypatch.setattr(cache, "get_cache_client", lambda: BrokenClient())

    assert cache.get_json("x") is None


def test_set_json_ignores_redis_errors(monkeypatch):
    class BrokenClient:
        def setex(self, key, ttl, value):
            raise redis.RedisError("down")

    monkeypatch.setattr(cache, "get_cache_client", lambda: BrokenClient())

    cache.set_json("x", {"ok": True})
