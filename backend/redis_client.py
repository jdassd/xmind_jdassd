from __future__ import annotations

import asyncio
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def init_redis(url: str, retries: int = 10, delay: float = 1.0) -> None:
    global _redis
    _redis = aioredis.from_url(url, decode_responses=True)
    # Retry ping — Redis may still be starting up inside the same container
    for attempt in range(1, retries + 1):
        try:
            await _redis.ping()
            logger.info("Redis connected at %s", url)
            return
        except (aioredis.ConnectionError, OSError) as exc:
            if attempt == retries:
                raise
            logger.warning(
                "Redis not ready (attempt %d/%d): %s — retrying in %.1fs",
                attempt, retries, exc, delay,
            )
            await asyncio.sleep(delay)


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
