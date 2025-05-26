# game_server\app_cache\redis_client.py

import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis

from game_server.settings import REDIS_PASSWORD, REDIS_URL

class RedisClient:
    def __init__(self, redis_url: str = REDIS_URL, max_connections: int = 10, redis_password: str = REDIS_PASSWORD):
        self.logger = logging.getLogger("redis_client")
        try:
            self.redis = aioredis.from_url(
                redis_url,
                password=redis_password,  # 🔥 Явно передаём пароль
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                max_connections=max_connections,
            )
        except Exception as e:
            self.logger.critical(f"Redis connection failed: {str(e)}")
            raise ConnectionError(f"Redis connection error: {str(e)}")
        
    async def ping(self) -> bool:
        """Проверка подключения к Redis с логированием."""
        try:
            is_alive = await self.redis.ping()
            if not is_alive:
                self.logger.warning("Redis ping returned False (сервер перегружен?)")
            return is_alive
        except Exception as e:
            self.logger.error(f"Redis ping failed: {str(e)}")
            return False
        
    # ✅ Pub/Sub
    def pubsub(self):
        """Создание Pub/Sub клиента для Redis."""
        return self.redis.pubsub()

    # ✅ Транзакции
    def pipeline(self):
        """Создание Redis-транзакции."""
        return self.redis.pipeline()

    # ✅ Удаление без блокировки
    async def unlink(self, key: str):
        """Асинхронное удаление ключа без блокировки."""
        await self.redis.unlink(key)

    # ✅ Управление TTL
    async def expire(self, key: str, seconds: int):
        """Установка времени жизни ключа."""
        await self.redis.expire(key, seconds)

    async def ttl(self, key: str):
        """Получение оставшегося времени жизни ключа."""
        return await self.redis.ttl(key)

    # ✅ Инкремент и декремент
    async def incr(self, key: str, amount: int = 1):
        """Увеличение значения."""
        return await self.redis.incr(key, amount)

    async def decr(self, key: str, amount: int = 1):
        """Уменьшение значения."""
        return await self.redis.decr(key, amount)

    # ✅ Сортированные множества (Leaderboard)
    async def zadd(self, key: str, score: float, member: str):
        """Добавление элемента в сортированное множество."""
        await self.redis.zadd(key, {member: score})

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = True):
        """Получение элементов из сортированного множества."""
        return await self.redis.zrange(key, start, stop, withscores=withscores)

    async def hkeys(self, key: str):
        """Возвращает список всех полей (ключей) хэша в Redis."""
        return await self.redis.hkeys(key)

    # ✅ Хэши (структурированные данные)
    async def hset(self, key: str, field: str, value: str):
        """Установка поля в хэше."""
        await self.redis.hset(key, field, value)

    async def hget(self, key: str, field: str):
        """Получение поля из хэша."""
        return await self.redis.hget(key, field)

    async def hgetall(self, key: str):
        """Получение всех полей и значений из хэша."""
        return await self.redis.hgetall(key)

    # ✅ Блокировки (например, чтобы избежать гонки данных)
    async def setnx(self, key: str, value: str):
        """Запись ключа, если его ещё нет (атомарная операция)."""
        return await self.redis.setnx(key, value)

    async def publish(self, channel: str, message: str):
        """Публикует сообщение в указанный канал."""
        return await self.redis.publish(channel, message)    

    # ✅ Стандартные методы
    async def set(self, key: str, value: str):
        await self.redis.set(key, value)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str):
        return bool(await self.redis.exists(key))

    async def keys(self, pattern: str = "*"):
        return await self.redis.keys(pattern)

    async def rpush(self, key: str, value):
        return await self.redis.rpush(key, value)

    async def lrange(self, key: str, start: int, stop: int):
        return await self.redis.lrange(key, start, stop)

    async def ltrim(self, key: str, start: int, stop: int):
        await self.redis.ltrim(key, start, stop)

    async def llen(self, key: str):
        return await self.redis.llen(key)

    async def close(self):
        """Закрытие соединения с Redis."""
        await self.redis.aclose()

    async def get_task_keys(self, queue_name: str, use_lrange: bool = False):
        """Унифицированный метод для получения ключей задач."""
        if use_lrange:
            return await self.redis.lrange(queue_name, 0, -1)
        return await self.redis.keys(queue_name)
 
    async def get_tick_tasks(self, queue_name: str):
        """Получает список задач из очереди Redis."""
        return await self.redis.lrange(queue_name, 0, -1)

    async def hdel(self, key: str, *fields: str):
        """Удаление одного или нескольких полей из хэша Redis."""
        return await self.redis.hdel(key, *fields)
    
    async def set_json(self, key: str, value: dict):
        """Сериализует dict в JSON и сохраняет в Redis."""
        await self.redis.set(key, json.dumps(value))

    async def get_json(self, key: str) -> Optional[dict]:
        """Читает JSON из Redis и парсит в dict."""
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get(self, key: str, default: Any = None) -> Any:
        """Возвращает default, если ключа нет."""
        value = await self.redis.get(key)
        return value if value is not None else default
    
    
redis_client = RedisClient()

# 📌 Пример использования:
if __name__ == "__main__":
    import asyncio

    async def main():
        client = RedisClient()
        await client.set("test_key", "hello world")
        value = await client.get("test_key")
        print(f"Retrieved: {value}")
        await client.delete("test_key")
        await client.close()

    asyncio.run(main())
