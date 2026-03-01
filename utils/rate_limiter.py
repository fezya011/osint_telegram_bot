import asyncio
import redis.asyncio as redis
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:

    def __init__(self, redis_url: str, max_requests: int = 5, window: int = 60):
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window = window
        self.redis: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()

    async def init(self):
        if not self.redis:
            async with self._lock:
                if not self.redis:
                    try:
                        self.redis = await redis.from_url(
                            self.redis_url,
                            decode_responses=True,
                            socket_keepalive=True,
                            health_check_interval=30
                        )
                        logger.info("Redis connection established")
                    except Exception as e:
                        logger.error(f"Redis connection failed: {e}")
                        self.redis = None

    async def check(self, user_id: int) -> bool:
        await self.init()

        if self.redis:
            key = f"rate_limit:{user_id}"
            try:
                current = await self.redis.get(key)

                if current is None:
                    await self.redis.setex(key, self.window, 1)
                    return True
                else:
                    current_count = int(current)
                    if current_count < self.max_requests:
                        await self.redis.incr(key)
                        return True
                    else:
                        ttl = await self.redis.ttl(key)
                        logger.debug(f"User {user_id} rate limited, TTL: {ttl}s")
                        return False
            except redis.RedisError as e:
                logger.error(f"Redis error in rate limiter: {e}")
                return True
        else:
            return await self._check_memory(user_id)

    async def _check_memory(self, user_id: int) -> bool:
        if not hasattr(self, '_memory_storage'):
            self._memory_storage = {}
            self._memory_lock = asyncio.Lock()

        async with self._memory_lock:
            now = datetime.now()
            key = user_id

            if key not in self._memory_storage:
                self._memory_storage[key] = []

            self._memory_storage[key] = [
                ts for ts in self._memory_storage[key]
                if ts > now - timedelta(seconds=self.window)
            ]

            if len(self._memory_storage[key]) < self.max_requests:
                self._memory_storage[key].append(now)
                return True
            else:
                return False

    async def get_remaining(self, user_id: int) -> int:
        await self.init()

        if self.redis:
            key = f"rate_limit:{user_id}"
            try:
                current = await self.redis.get(key)
                if current is None:
                    return self.max_requests
                else:
                    return max(0, self.max_requests - int(current))
            except redis.RedisError:
                return self.max_requests
        else:
            if not hasattr(self, '_memory_storage'):
                return self.max_requests

            async with self._memory_lock:
                now = datetime.now()
                key = user_id
                if key not in self._memory_storage:
                    return self.max_requests

                self._memory_storage[key] = [
                    ts for ts in self._memory_storage[key]
                    if ts > now - timedelta(seconds=self.window)
                ]
                return max(0, self.max_requests - len(self._memory_storage[key]))

    async def reset(self, user_id: int):
        await self.init()

        if self.redis:
            key = f"rate_limit:{user_id}"
            try:
                await self.redis.delete(key)
            except redis.RedisError:
                pass
        else:
            if hasattr(self, '_memory_storage'):
                async with self._memory_lock:
                    self._memory_storage.pop(user_id, None)

    async def close(self):
        if self.redis:
            await self.redis.close()
            await self.redis.connection_pool.disconnect()
            logger.info("Redis connection closed")