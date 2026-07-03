"""Redis 工具类 — 缓存、分布式锁、JSON 序列化

提供：
- RedisClient: 轻量封装，自动从 settings 加载连接，Json 序列化
- cache_result: 函数结果缓存装饰器（可指定 TTL）
- 支持 FastAPI 依赖注入（get_redis）
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisClient:
    """异步 Redis 客户端封装"""

    def __init__(self, url: str | None = None):
        self._url = url or settings.REDIS_URL
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def init(self) -> None:
        """初始化连接池（应用启动时调用）。"""
        if self._client is not None:
            return
        self._pool = ConnectionPool.from_url(self._url, decode_responses=True)
        self._client = Redis.from_pool(self._pool)
        logger.info("✅ Redis 连接池已创建")

    async def close(self) -> None:
        """关闭连接池（应用关闭时调用）。"""
        if self._pool:
            await self._pool.disconnect()
            logger.info("👋 Redis 连接池已关闭")

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisClient 未初始化，请先调用 init()")
        return self._client

    # ── 基础操作 ──────────────────────────────────

    async def get(self, key: str) -> Any | None:
        """获取字符串值。"""
        val = await self.client.get(key)
        return val

    async def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """设置字符串值，可选过期时间（秒）。"""
        return await self.client.set(key, value, ex=expire)

    async def delete(self, *keys: str) -> int:
        """删除一个或多个键。"""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """判断键是否存在。"""
        return await self.client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间。"""
        return await self.client.expire(key, seconds)

    # ── JSON 存取 ─────────────────────────────────

    async def json_get(self, key: str) -> Any | None:
        """获取并反序列化 JSON 值。"""
        val = await self.client.get(key)
        return json.loads(val) if val else None

    async def json_set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """序列化为 JSON 并存入 Redis。"""
        return await self.client.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=expire)

    # ── 哈希操作 ──────────────────────────────────

    async def hget(self, name: str, key: str) -> Any | None:
        return await self.client.hget(name, key)

    async def hset(self, name: str, key: str, value: Any) -> int:
        return await self.client.hset(name, key, value)

    async def hgetall(self, name: str) -> dict:
        return await self.client.hgetall(name) or {}

    async def hdel(self, name: str, *keys: str) -> int:
        return await self.client.hdel(name, *keys)

    # ── 缓存装饰器 ────────────────────────────────

    @staticmethod
    def cache_result(key_prefix: str, expire: int = 300):
        """函数结果缓存装饰器（缓存方法返回值）。

        Usage::

            @RedisClient.cache_result("user:profile", expire=600)
            async def get_user_profile(user_id: str) -> dict:
                ...
        """

        def decorator(func):
            async def wrapper(*args, **kwargs) -> Any:
                # 构建缓存键：{key_prefix}:{first_arg}
                cache_key = f"{key_prefix}:{args[0] if args else 'default'}"
                redis = await _get_redis_instance()
                # 这里不做自动注入，建议直接使用 RedisClient 实例
                cached = await redis.json_get(cache_key)
                if cached is not None:
                    return cached
                result = await func(*args, **kwargs)
                await redis.json_set(cache_key, result, expire=expire)
                return result
            return wrapper
        return decorator


# ── 全局单例 ──────────────────────────────────────

redis_client = RedisClient()


# ── 依赖注入 ─────────────────────────────────────


async def get_redis() -> AsyncGenerator[Redis, Any]:
    """FastAPI 依赖注入：获取原生 Redis 实例。"""
    yield redis_client.client


async def get_redis_client() -> AsyncGenerator[RedisClient, Any]:
    """FastAPI 依赖注入：获取 RedisClient 封装实例。"""
    yield redis_client


async def _get_redis_instance() -> RedisClient:
    """内部辅助：获取 RedisClient（已初始化检查）。"""
    if redis_client._client is None:
        await redis_client.init()
    return redis_client
