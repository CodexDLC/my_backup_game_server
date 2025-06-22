# game_server/Logic/InfrastructureLogic/app_cache/central_redis_client.py

import json
import logging
from typing import Any, Dict, List, Optional, Union
import uuid # 🔥 ИЗМЕНЕНИЕ: Добавляем Union
import msgpack
import redis.asyncio as redis_asyncio

from game_server.config.settings_core import REDIS_PASSWORD, REDIS_POOL_SIZE, REDIS_URL


class CentralRedisClient:
    """
    Низкоуровневый клиент для взаимодействия с центральным Redis-сервером Backend'а.
    Использует redis-py (версии 5+) для асинхронной работы с Redis.
    Этот клиент управляет собственным пулом подключений.
    """
    def __init__(
        self,
        redis_url: str = REDIS_URL,
        max_connections: int = REDIS_POOL_SIZE,
        redis_password: str = REDIS_PASSWORD
    ):
        self.logger = logging.getLogger("central_redis_client")
        self._redis_url = redis_url
        self._max_connections = max_connections
        self._redis_password = redis_password
        self.redis: Optional[redis_asyncio.Redis] = None
        self.redis_raw: Optional[redis_asyncio.Redis] = None
        self.logger.info("✨ CentralRedisClient инициализирован, ожидание подключения.")

    async def connect(self):
        """
        Асинхронно инициализирует соединение (пул) с Redis.
        """
        if self.redis is None:
            self.logger.info(f"🔧 Подключение к центральному Redis: {self._redis_url}...")
            try:
                self.redis = redis_asyncio.from_url(
                    self._redis_url,
                    password=self._redis_password,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                self.redis_raw = redis_asyncio.from_url(
                    self._redis_url,
                    password=self._redis_password,
                    decode_responses=False,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )

                await self.redis.ping()
                await self.redis_raw.ping()
                self.logger.info(f"✅ Подключение к центральному Redis успешно установлено: {self._redis_url}")
            except Exception as e:
                self.logger.critical(f"❌ Критическая ошибка при подключении к Redis: {e}", exc_info=True)
                raise
        else:
            self.logger.debug("Соединение с Redis уже инициализировано.")

    async def hgetall_json(self, name: str) -> Optional[Dict[str, Any]]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return None
        data = await self.redis.hgetall(name)
        if data:
            try:
                return {k: json.loads(v) for k, v in data.items()}
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка десериализации JSON в hgetall_json для ключа '{name}': {e}")
                return None
        return None

    async def hsetall_json(self, name: str, mapping: Dict[str, Any]):        
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return

        def json_serializer(obj):
            if isinstance(obj, (bytes, str, int, float)):
                return obj
            if isinstance(obj, bool):
                return obj
            if isinstance(obj, (list, dict)):
                return obj
            if isinstance(obj, uuid.UUID): # Если у вас есть UUID, явно преобразуйте его
                return str(obj)
            # Если поле имеет значение None, json.dumps по умолчанию преобразует его в null.
            # Если у вас есть другие типы, которые нужно сериализовать, добавьте их здесь.
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

        json_mapping = {k: json.dumps(v, default=json_serializer) for k, v in mapping.items()} # <-- ИЗМЕНЕНО: используем пользовательский сериализатор
        
        await self.redis.hset(name, mapping=json_mapping)

    async def get_json(self, key: str) -> Optional[dict]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return None
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка десериализации JSON в get_json для ключа '{key}': {e}")
                return None
        return None

    async def set_json(self, key: str, value: dict, ex: Optional[int] = None):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        await self.redis.set(key, json.dumps(value, default=str), ex=ex)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        return await self.redis.set(key, value, ex=ex)

    async def get(self, key: str) -> Optional[str]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return None
        return await self.redis.get(key)

    async def delete(self, *keys: str) -> int:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return 0
        return await self.redis.delete(*keys)

    async def expire(self, key: str, ttl: int):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        await self.redis.expire(key, ttl)

    async def exists(self, *keys: str) -> int:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return 0
        return await self.redis.exists(*keys)

    async def keys(self, pattern: str = "*") -> List[str]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return []
        return await self.redis.keys(pattern)
        
    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return []
        return await self.redis.mget(keys)     
    
    async def scan_iter(self, pattern: str = "*", count: Optional[int] = None):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        async for key in self.redis.scan_iter(pattern, count=count):
            yield key

    async def rpush(self, key: str, *values: Any):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        return await self.redis.rpush(key, *values)

    async def lrange(self, key: str, start: int, stop: int) -> List[str]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return []
        return await self.redis.lrange(key, start, stop)

    async def ltrim(self, key: str, start: int, stop: int):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        await self.redis.ltrim(key, start, stop)

    async def llen(self, key: str) -> int:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return 0
        return await self.redis.llen(key)
        
    async def hget(self, name: str, key: str) -> Optional[str]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return None
        return await self.redis.hget(name, key)

    async def hset(self, name: str, key: str, value: Any):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        return await self.redis.hset(name, key, value)

    async def hdel(self, name: str, *keys: str):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        return await self.redis.hdel(name, *keys)

    async def hgetall(self, name: str) -> Dict[str, str]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return {}
        return await self.redis.hgetall(name)

    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return 0
        return await self.redis.hincrby(name, key, amount)

    async def hmget(self, name: str, keys: List[str]) -> List[Optional[str]]:
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return []
        return await self.redis.hmget(name, keys)

    async def hgetall_raw(self, name: str) -> Dict[bytes, bytes]:
        if self.redis_raw is None: self.logger.error("Redis-соединение (сырое) не инициализировано."); return {}
        return await self.redis_raw.hgetall(name)

    async def hset_raw(self, name: str, key: Union[str, bytes], value: Union[str, bytes]):
        if self.redis_raw is None: self.logger.error("Redis-соединение (сырое) не инициализировано."); return
        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
        value_bytes = value.encode('utf-8') if isinstance(value, str) else value
        return await self.redis_raw.hset(name, key_bytes, value_bytes)

    async def hincrby_raw(self, name: str, key: Union[str, bytes], amount: int = 1) -> int:
        if self.redis_raw is None: self.logger.error("Redis-соединение (сырое) не инициализировано."); return 0
        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
        return await self.redis_raw.hincrby(name, key_bytes, amount)

    def pipeline(self) -> redis_asyncio.client.Pipeline:
        if self.redis is None:
            self.logger.critical("Redis-соединение не инициализировано! Невозможно создать пайплайн.")
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self.redis.pipeline()

    def pipeline_raw(self) -> redis_asyncio.client.Pipeline:
        if self.redis_raw is None:
            self.logger.critical("Redis-соединение (сырое) не инициализировано! Невозможно создать пайплайн.")
            raise RuntimeError("Raw Redis client not connected. Call connect() first.")
        return self.redis_raw.pipeline()

    async def publish(self, channel: str, message: Any):
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        return await self.redis.publish(channel, message)

    async def subscribe(self, channel: str):
        if self.redis is None:
            self.logger.critical("Redis-соединение не инициализировано! Невозможно подписаться.")
            raise RuntimeError("Redis client not connected. Call connect() first.")
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    async def hsetall_msgpack(self, name: str, mapping: Dict[str, bytes]): # <--- Изменено: Ожидаем Dict[str, bytes]
        """
        Сохраняет словарь в Redis HASH. Значения уже должны быть в формате MsgPack байтов.
        """
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        # Ключи в байты, значения уже байты
        msgpack_mapping_bytes = {k.encode('utf-8'): v for k, v in mapping.items()} 
        await self.redis.hset(name, mapping=msgpack_mapping_bytes)

    async def hgetall_msgpack(self, name: str) -> Optional[Dict[str, Any]]: # <--- Изменено: возвращаем Any, т.к. десериализация происходит здесь
        """
        Извлекает данные из Redis HASH, десериализуя значения из MsgPack.
        """
        if self.redis_raw is None: self.logger.error("Redis-соединение (сырое) не инициализировано."); return None
        raw_data = await self.redis_raw.hgetall(name)
        if raw_data:
            try:
                # Декодируем ключи обратно в строки, десериализуем значения из MsgPack
                return {k.decode('utf-8'): msgpack.loads(v, raw=False) for k, v in raw_data.items()}
            except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackValueError) as e:
                self.logger.error(f"Ошибка десериализации MsgPack в hgetall_msgpack для ключа '{name}': {e}")
                return None
        return None

    async def set_msgpack(self, key: str, value: bytes, ex: Optional[int] = None): # <--- Изменено: Ожидаем bytes
        """
        Сохраняет значение в Redis STRING. Значение уже должно быть в формате MsgPack байтов.
        """
        if self.redis is None: self.logger.error("Redis-соединение не инициализировано."); return
        await self.redis.set(key, value, ex=ex) # value уже bytes

    async def get_msgpack(self, key: str) -> Optional[Any]: # <--- Изменено: возвращаем Any
        """
        Извлекает значение из Redis STRING, десериализуя его из MsgPack.
        """
        if self.redis_raw is None: self.logger.error("Redis-соединение (сырое) не инициализировано."); return None
        packed_value = await self.redis_raw.get(key)
        if packed_value:
            try:
                return msgpack.loads(packed_value, raw=False)
            except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackValueError) as e:
                self.logger.error(f"Ошибка десериализации MsgPack в get_msgpack для ключа '{key}': {e}")
                return None
        return None

    async def close(self):
        if self.redis:
            await self.redis.close()
            self.logger.info("✅ Основное Redis-соединение успешно закрыто.")
        if self.redis_raw:
            await self.redis_raw.close()
            self.logger.info("✅ Сырое Redis-соединение успешно закрыто.")
        self.redis = None
        self.redis_raw = None