import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import USE_POSTGRES, USE_REDIS

logger = logging.getLogger(__name__)

try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not installed, PostgreSQL disabled")

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis.asyncio not installed, Redis disabled")

pg_pool = None
redis_client = None

_memory_storage = []
_memory_counter = 0


async def init_db(dsn: str, redis_url: str):
    global pg_pool, redis_client

    if USE_POSTGRES and ASYNCPG_AVAILABLE:
        try:
            pg_pool = await asyncpg.create_pool(
                dsn,
                min_size=1,
                max_size=2,
                command_timeout=5
            )
            logger.info("PostgreSQL pool created")

            async with pg_pool.acquire() as conn:
                await conn.execute("""
                                   CREATE TABLE IF NOT EXISTS searches
                                   (
                                       id
                                       SERIAL
                                       PRIMARY
                                       KEY,
                                       user_id
                                       BIGINT
                                       NOT
                                       NULL,
                                       search_type
                                       VARCHAR
                                   (
                                       20
                                   ) NOT NULL,
                                       query TEXT NOT NULL,
                                       result JSONB,
                                       timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                       )
                                   """)
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON searches(user_id)")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            pg_pool = None
    else:
        logger.info("PostgreSQL disabled by config or not available")

    if USE_REDIS and REDIS_AVAILABLE:
        try:
            redis_client = await redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2
            )
            await redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_client = None
    else:
        logger.info("Redis disabled by config or not available")


async def close_db():
    global pg_pool, redis_client

    if pg_pool:
        await pg_pool.close()
        logger.info("PostgreSQL pool closed")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def save_search(user_id: int, search_type: str, query: str, result: Dict[str, Any]):
    global _memory_storage, _memory_counter

    if pg_pool is not None:
        try:
            async with pg_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO searches (user_id, search_type, query, result) VALUES ($1, $2, $3, $4)",
                    user_id, search_type, query, json.dumps(result, ensure_ascii=False, default=str)
                )
            logger.debug(f"Saved to PostgreSQL: {search_type} - {query}")
            return
        except Exception as e:
            logger.error(f"PostgreSQL save failed: {e}")

    _memory_counter += 1
    entry = {
        "id": _memory_counter,
        "user_id": user_id,
        "search_type": search_type,
        "query": query,
        "result": result,
        "timestamp": datetime.now()
    }
    _memory_storage.append(entry)
    if len(_memory_storage) > 1000:
        _memory_storage = _memory_storage[-1000:]
    logger.debug(f"Saved to memory: {search_type} - {query}")

    if redis_client is not None:
        try:
            cache_key = f"search:{search_type}:{query}"
            await redis_client.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False, default=str))
        except Exception as e:
            logger.warning(f"Redis cache failed: {e}")


async def get_search_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    if pg_pool is not None:
        try:
            async with pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT search_type, query, timestamp FROM searches WHERE user_id = $1 ORDER BY timestamp DESC LIMIT $2",
                    user_id, limit
                )
            if rows:
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}")

    user_entries = [e for e in _memory_storage if e["user_id"] == user_id]
    user_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    return [
        {
            "search_type": e["search_type"],
            "query": e["query"],
            "timestamp": e["timestamp"]
        }
        for e in user_entries[:limit]
    ]

async def get_cached_result(search_type: str, query: str) -> Optional[Dict[str, Any]]:
    if redis_client is not None:
        try:
            cache_key = f"search:{search_type}:{query}"
            data = await redis_client.get(cache_key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
    return None