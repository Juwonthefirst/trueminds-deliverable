# type: ignore

import redis.asyncio as async_redis
import os
from .utils import load_enviroment_variables

load_enviroment_variables()

redis_url = os.getenv("REDIS_URL")
if redis_url is None:
    raise ValueError("REDIS_URL environment variable is not set")


class Cache:
    def __init__(self):
        pool = async_redis.ConnectionPool.from_url(url=redis_url, decode_responses=True)
        self.redis = async_redis.Redis(connection_pool=pool)

    async def set(self, key: str, value, expiry_time=60):
        await self.redis.set(key, value, ex=expiry_time)

    async def set_hash(
        self,
        key: str,
        mapping,
        expiry_time,
    ):
        await self.redis.hset(key, mapping=mapping)
        if expiry_time:
            await self.redis.expire(key, expiry_time)

    async def set_hash_field(self, hash_key, field_key, value):
        await self.redis.hset(hash_key, field_key, value)

    async def delete_hash_field(self, hash_key, field_key):
        await self.redis.hdel(hash_key, field_key)

    async def increase_hash_field(self, hash_key, field_key, amount=1):
        return await self.redis.hincrby(hash_key, field_key, amount)

    async def get_hash_field(self, hash_key, field_key):
        return await self.redis.hget(hash_key, field_key)

    async def get_hash(self, hash_key):
        return await self.redis.hgetall(hash_key)

    async def get(self, key):
        return await self.redis.get(key)

    async def delete(self, key):
        await self.redis.delete(key)

    async def set_expire_time(self, key: str, amount: int):
        await self.redis.expire(key, amount)


cache = Cache()
