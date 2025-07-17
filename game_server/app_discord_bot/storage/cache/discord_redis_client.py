# Discord_API\app_cache\discord_redis_client.py

import json
import logging
from typing import Any, List, Optional, Union
import redis.asyncio as aioredis

from game_server.app_discord_bot.config.discord_settings import REDIS_BOT_LOCAL_PASSWORD, REDIS_BOT_LOCAL_POOL_SIZE, REDIS_BOT_LOCAL_URL


class DiscordRedisClient:
    """
    Низкоуровневый клиент для взаимодействия с локальным Redis-сервером Discord-бота.
    Предоставляет базовые асинхронные операции Redis.
    """
    def __init__(
        self,
        redis_url: str = REDIS_BOT_LOCAL_URL,
        max_connections: int = REDIS_BOT_LOCAL_POOL_SIZE,
        redis_password: Optional[str] = REDIS_BOT_LOCAL_PASSWORD
    ):
        self.logger = logging.getLogger("discord_redis_client")
        try:
            self.redis = aioredis.from_url(
                redis_url,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                max_connections=max_connections,
            )
            self.logger.info(f"✅ Подключение к локальному Redis бота успешно: {redis_url}")
        except Exception as e:
            self.logger.critical(f"❌ Ошибка подключения к локальному Redis бота: {str(e)}", exc_info=True)
            raise ConnectionError(f"Ошибка подключения к локальному Redis бота: {str(e)}")

    async def ping(self) -> bool:
        """Проверка подключения к Redis с логированием."""
        try:
            is_alive = await self.redis.ping()
            if not is_alive:
                self.logger.warning("Локальный Redis бота ping вернул False (сервер перегружен?)")
            return is_alive
        except Exception as e:
            self.logger.error(f"Локальный Redis бота ping failed: {str(e)}")
            return False

    def pubsub(self):
        """Создание Pub/Sub клиента для Redis (для внутренних нужд бота)."""
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
        
    # 👇 ДОБАВЬТЕ ЭТОТ НОВЫЙ МЕТОД
    async def hmset(self, key: str, data: dict):
        if not data:
            return
        await self.redis.hset(key, mapping=data)
        
    async def hget(self, key: str, field: str):
        """Получение поля из хэша."""
        return await self.redis.hget(key, field)

    async def hgetall(self, key: str):
        """Получение всех полей и значений из хэша."""
        return await self.redis.hgetall(key)

    async def hdel(self, key: str, *fields: str):
        """Удаление одного или нескольких полей из хэша Redis."""
        return await self.redis.hdel(key, *fields)

    async def setnx(self, key: str, value: str):
        """Запись ключа, если его ещё нет (атомарная операция)."""
        return await self.redis.setnx(key, value)

    async def publish(self, channel: str, message: str):
        """Публикует сообщение в указанный канал (если боту нужен внутренний Pub/Sub)."""
        return await self.redis.publish(channel, message)

    async def set(self, key: str, value: str):
        await self.redis.set(key, value)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str):
        return bool(await self.redis.exists(key))

    async def keys(self, pattern: str = "*"):
        """
        Используйте с осторожностью на больших базах данных.
        Для продакшена предпочтительнее SCAN.
        """
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
        """
        Унифицированный метод для получения ключей задач.
        (Оставлен, если бот будет иметь свои внутренние очереди в локальном Redis).
        """
        if use_lrange:
            return await self.redis.lrange(queue_name, 0, -1)
        return await self.redis.keys(queue_name)

    async def get_tick_tasks(self, queue_name: str):
        """
        Получает список задач из очереди Redis.
        (Оставлен, если бот будет иметь свои тики в локальном Redis).
        """
        return await self.redis.lrange(queue_name, 0, -1)

    async def set_json(self, key: str, value: dict):
        """Сериализует dict в JSON и сохраняет в Redis."""
        await self.redis.set(key, json.dumps(value))

    async def get_json(self, key: str) -> Optional[dict]:
        """Читает JSON из Redis и парсит в dict."""
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get_or_default(self, key: str, default: Any = None) -> Any:
        """Возвращает default, если ключа нет."""
        value = await self.redis.get(key)
        return value if value is not None else default
    
            # ДОБАВЬТЕ ЭТОТ МЕТОД
    async def hmset(self, key: str, data: dict):
        """Устанавливает несколько полей в хеше за один раз."""
        # Используем пайплайн для эффективности
        async with self.redis.pipeline() as pipe:
            for field, value in data.items():
                pipe.hset(key, field, value)
            await pipe.execute()

    # ДОБАВЬТЕ ЭТОТ МЕТОД
    async def sadd(self, key: str, *members):
        """Добавляет один или несколько элементов в множество (Set)."""
        if not members:
            return
        await self.redis.sadd(key, *members)

    async def srem(self, key: str, *members):
        """Удаляет один или несколько элементов из множества (Set)."""
        if not members:
            return
        await self.redis.srem(key, *members)
        

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        """
        Устанавливает значение ключа с заданным временем жизни (TTL) в секундах.
        """
        print(f"--- REDIS DEBUG --- Вызван set_with_ttl для ключа: {key}")
        print(f"--- REDIS DEBUG --- Полученный TTL: {ttl}, ЕГО ТИП: {type(ttl)}")
      
        try:
            await self.redis.set(key, value, ex=ttl)
            self.logger.debug(f"Ключ '{key}' установлен с TTL: {ttl}s")
        except Exception as e:
            self.logger.error(f"Ошибка при установке ключа '{key}' с TTL: {e}", exc_info=True)
            
    async def eval(self, script: Union[str, bytes], keys: List[Any] = None, args: List[Any] = None) -> Any:
        """
        Выполняет Lua-скрипт на сервере Redis.
        Делегирует вызов базовому Redis-клиенту.
        """
        if keys is None:
            keys = []
        if args is None:
            args = []
        try:
            # Важно: eval ожидает ключи и аргументы в байтах, если decode_responses=False
            encoded_keys = [k.encode('utf-8') if isinstance(k, str) else k for k in keys]
            encoded_args = [a.encode('utf-8') if isinstance(a, str) else a for a in args]

            # 🔥 ИЗМЕНЕНО: Передаем numkeys (количество ключей) и распаковываем списки keys и args
            result = await self.redis.eval(script, len(encoded_keys), *encoded_keys, *encoded_args)
            return result
        except Exception as e:
            raise

# Создаем единственный экземпляр клиента для локального Redis бота
discord_redis_client = DiscordRedisClient()

# 📌 Пример использования: (Этот блок будет запускаться только при прямом запуске файла)
if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv

    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')))

    async def test_discord_redis_client():
        print("Тестирование DiscordRedisClient...")
        try:
            client = DiscordRedisClient() 
            await client.set("test_bot_key", "hello from discord bot's local redis")
            value = await client.get("test_bot_key")
            print(f"Retrieved from local Redis: {value}")
            await client.delete("test_bot_key")
            print("test_bot_key удален.")

            await client.set_json("test_bot_json_key", {"user_id": 123, "data": "some_data"})
            json_data = await client.get_json("test_bot_json_key")
            print(f"Retrieved JSON: {json_data}")
            await client.delete("test_bot_json_key")
            print("test_bot_json_key удален.")

        except ConnectionError as ce:
            print(f"Ошибка подключения Redis: {ce}. Убедитесь, что Redis запущен и REDIS_BOT_LOCAL_URL корректен.")
        except Exception as e:
            print(f"Произошла ошибка во время теста: {e}")
        finally:
            if 'client' in locals() and hasattr(client, 'close'):
                await client.close()
            print("Соединение с локальным Redis бота закрыто (если было открыто).")           
            
            
            
            

    asyncio.run(test_discord_redis_client())
    
    
