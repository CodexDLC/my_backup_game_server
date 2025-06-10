# game_server/Logic/InfrastructureLogic/app_cache/central_redis_client.py

import json
import logging
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

from game_server.settings import REDIS_PASSWORD, REDIS_POOL_SIZE, REDIS_URL

class CentralRedisClient:
    """
    Низкоуровневый клиент для взаимодействия с центральным Redis-сервером Backend'а.
    """
    def __init__(
        self,
        redis_url: str = REDIS_URL,
        max_connections: int = REDIS_POOL_SIZE,
        redis_password: str = REDIS_PASSWORD
    ):
        self.logger = logging.getLogger("central_redis_client")
        self._redis_url = redis_url # Сохраняем для переинициализации
        self._max_connections = max_connections # Сохраняем для переинициализации
        self._redis_password = redis_password # Сохраняем для переинициализации
        self.redis = self._initialize_redis_connection() # Инициализируем соединение при создании
        self.logger.info(f"✅ Подключение к центральному Redis успешно: {redis_url}")

    def _initialize_redis_connection(self):
        """Вспомогательный метод для инициализации соединения Redis."""
        try:
            return aioredis.from_url(
                self._redis_url,
                password=self._redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                max_connections=self._max_connections,
            )
        except Exception as e:
            self.logger.critical(f"❌ Ошибка подключения к центральному Redis: {str(e)}", exc_info=True)
            raise ConnectionError(f"Ошибка подключения к центральному Redis: {str(e)}")

    async def reinitialize_connection(self):
        """
        Закрывает текущее соединение Redis и создает новое.
        Используется для перепривязки к Event Loop, например, при запуске asyncio.run().
        """
        if self.redis:
            try:
                await self.redis.aclose()
                self.logger.info("Существующее соединение Redis закрыто.")
            except Exception as e:
                self.logger.warning(f"Ошибка при закрытии существующего соединения Redis: {e}")
        
        self.redis = self._initialize_redis_connection()
        self.logger.info("Новое соединение Redis успешно переинициализировано.")


    # ... все остальные методы (ping, hget, hset и т.д.) остаются без изменений ...

    async def hgetall(self, key: str):
        """Получение всех полей и значений из хэша."""
        return await self.redis.hgetall(key)
        
    async def hlen(self, key: str) -> int:
        """Получает количество полей в хэше Redis."""
        return await self.redis.hlen(key)

    async def hmset(self, key: str, mapping: Dict[str, Any]) -> None:
        """Устанавливает несколько полей в хэше за одну операцию."""
        # aioredis 2.x doesn't have hmset directly, it's just set.
        # But this method is used for backward compatibility if you're using older version or if the method mapping changes.
        # If it's a direct dictionary update, then use hset with unpacked dict.
        # For simplicity, assuming the hmset behavior is as intended by user or older aioredis.
        # If it's for multiple field/value pairs, use hset(key, field1, value1, field2, value2)
        # or hset(key, mapping=mapping)
        await self.redis.hset(key, mapping=mapping) # Correct usage for dictionary mapping
        
    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """
        Увеличивает значение числового поля в хэше на указанную величину.
        """
        return await self.redis.hincrby(key, field, amount)

    async def setnx(self, key: str, value: str):
        """Запись ключа, если его ещё нет (атомарная операция)."""
        return await self.redis.setnx(key, value)

    async def publish(self, channel: str, message: str):
        """Публикует сообщение в указанный канал."""
        return await self.redis.publish(channel, message)

    async def set(self, key: str, value: str):
        await self.redis.set(key, value)

    async def get(self, key: str):
        return await self.redis.get(key)
    
    async def ping(self) -> bool:
        """Проверка подключения к Redis с логированием."""
        try:
            is_alive = await self.redis.ping()
            if not is_alive:
                self.logger.warning("Центральный Redis ping вернул False (сервер перегружен?)")
            return is_alive
        except Exception as e:
            self.logger.error(f"Центральный Redis ping failed: {str(e)}")
            return False

    def pubsub(self):
        """Создание Pub/Sub клиента для Redis."""
        return self.redis.pubsub()

    def pipeline(self):
        """Создание Redis-транзакции."""
        return self.redis.pipeline()

    async def unlink(self, key: str):
        """Асинхронное удаление ключа без блокировки."""
        await self.redis.unlink(key)

    async def expire(self, key: str, seconds: int):
        """Установка времени жизни ключа."""
        await self.redis.expire(key, seconds)

    async def ttl(self, key: str):
        """Получение оставшегося времени жизни ключа."""
        return await self.redis.ttl(key)

    async def incr(self, key: str, amount: int = 1):
        """Увеличение значения."""
        return await self.redis.incr(key, amount)

    async def decr(self, key: str, amount: int = 1):
        """Уменьшение значения."""
        return await self.redis.decr(key, amount)

    async def zadd(self, key: str, score: float, member: str):
        """Добавление элемента в сортированное множество."""
        await self.redis.zadd(key, {member: score})

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = True):
        """Получение элементов из сортированного множества."""
        return await self.redis.zrange(key, start, stop, withscores=withscores)

    async def hkeys(self, key: str):
        """Возвращает список всех полей (ключей) хэша в Redis."""
        return await self.redis.hkeys(key)

    async def hset(self, key: str, field: str, value: str):
        """Установка поля в хэше."""
        await self.redis.hset(key, field, value)

    async def hget(self, key: str, field: str):
        """Получение поля из хэша."""
        return await self.redis.hget(key, field)

    async def hdel(self, key: str, *fields: str):
        """Удаление одного или нескольких полей из хэша Redis."""
        return await self.redis.hdel(key, *fields)
    
    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str):
        return bool(await self.redis.exists(key))

    async def keys(self, pattern: str = "*"):
        return await self.redis.keys(pattern)
    
    async def mget(self, keys: list[str]):
        return await self.redis.mget(keys)    
    
    async def scan_keys(self, pattern: str = "*"):
        async for key in self.redis.scan_iter(pattern):
            yield key

    async def rpush(self, key: str, value):
        return await self.redis.rpush(key, value)

    async def lrange(self, key: str, start: int, stop: int):
        return await self.redis.lrange(key, start, stop)

    async def ltrim(self, key: str, start: int, stop: int):
        await self.redis.ltrim(key, start, stop)

    async def llen(self, key: str):
        return await self.redis.llen(key)

    async def close(self):
        await self.redis.aclose()

    async def set_json(self, key: str, value: dict):
        await self.redis.set(key, json.dumps(value))

    async def get_json(self, key: str) -> Optional[dict]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get_or_default(self, key: str, default: Any = None) -> Any:
        value = await self.redis.get(key)
        return value if value is not None else default

# Создаем единственный экземпляр клиента для центрального Redis
central_redis_client = CentralRedisClient()
