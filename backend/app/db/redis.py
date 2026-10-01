"""
Redis client + higher-level helpers.

Redis has four real responsibilities in this app:
  1. Response caching (dashboard stats, search results, node lookups)
  2. Rate limiting (sliding counters per user/IP)
  3. "Recently viewed" node tracking (capped list per user)
  4. "Popular nodes" tracking (sorted set, incremented on view)

Everything here is isolated behind this module so the rest of the app
never talks to redis.asyncio directly.
"""
import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings

redis_client: redis.Redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


# ---------------------------------------------------------------------------
# Generic cache helpers
# ---------------------------------------------------------------------------
async def cache_get(key: str) -> Optional[Any]:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)


async def cache_delete(*keys: str) -> None:
    if keys:
        await redis_client.delete(*keys)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern, e.g. 'search:42:*'."""
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=200)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break


# ---------------------------------------------------------------------------
# Rate limiting (fixed window counter)
# ---------------------------------------------------------------------------
async def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
    """Returns (allowed, remaining)."""
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)
    allowed = current <= limit
    remaining = max(0, limit - current)
    return allowed, remaining


# ---------------------------------------------------------------------------
# Recently viewed nodes (capped list, most-recent-first)
# ---------------------------------------------------------------------------
async def push_recent_node(user_id: str, node_id: str, cap: int = 20) -> None:
    key = f"recent:user:{user_id}"
    await redis_client.lrem(key, 0, node_id)
    await redis_client.lpush(key, node_id)
    await redis_client.ltrim(key, 0, cap - 1)


async def get_recent_nodes(user_id: str) -> list[str]:
    return await redis_client.lrange(f"recent:user:{user_id}", 0, -1)


# ---------------------------------------------------------------------------
# Popular nodes (sorted set, score = access count)
# ---------------------------------------------------------------------------
async def bump_popular_node(user_id: str, node_id: str) -> None:
    await redis_client.zincrby(f"popular:user:{user_id}", 1, node_id)


async def get_popular_nodes(user_id: str, top_n: int = 10) -> list[tuple[str, float]]:
    results = await redis_client.zrevrange(
        f"popular:user:{user_id}", 0, top_n - 1, withscores=True
    )
    return results


# ---------------------------------------------------------------------------
# JWT revocation (blacklist by jti)
# ---------------------------------------------------------------------------
async def blacklist_jti(jti: str, seconds_until_expiry: int) -> None:
    """Marks a token's jti as revoked until its natural expiry. Used on
    logout so a token that leaked or was copied elsewhere stops working
    immediately, instead of remaining valid until it expires on its own
    (the gap in a purely stateless JWT scheme)."""
    if seconds_until_expiry <= 0:
        return  # already expired naturally, nothing to do
    await redis_client.set(f"blacklist:{jti}", "1", ex=seconds_until_expiry)


async def is_jti_blacklisted(jti: str) -> bool:
    return await redis_client.exists(f"blacklist:{jti}") == 1
