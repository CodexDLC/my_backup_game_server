import redis.asyncio as aioredis
from game_server.config.redis_config import REDIS_URL

class RedisClient:
    def __init__(self, redis_url: str = REDIS_URL):
        """Инициализация клиента Redis."""
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        """Подключение к Redis."""
        self.redis = aioredis.Redis.from_url(self.redis_url, decode_responses=True)
        print(f"✅ Подключено к Redis по адресу {self.redis_url}")

    async def set(self, key: str, value: str):
        """Установка значения в Redis."""
        await self.redis.set(key, value)
        print(f"🔹 Установлено: {key} → {value}")

    async def get(self, key: str):
        """Получение значения из Redis."""
        value = await self.redis.get(key)
        if value is None:
            print(f"⚠️ Ключ {key} не найден!")
            return None
        print(f"🔹 Получено: {key} → {value}")
        return value

    async def delete(self, key: str):
        """Удаление ключа из Redis."""
        await self.redis.delete(key)
        print(f"❌ Ключ {key} удалён")

    async def exists(self, key: str):
        """Проверка существования ключа в Redis."""
        exists = await self.redis.exists(key)
        print(f"🔎 Ключ {key} {'существует' if exists else 'не найден'}")
        return bool(exists)

    async def close(self):
        """Закрытие соединения с Redis."""
        await self.redis.aclose()
        print("🚪 Соединение с Redis закрыто")

# Пример использования
async def main():
    redis_client = RedisClient()
    await redis_client.connect()
    
    await redis_client.set("test_key", "hello world")
    await redis_client.get("test_key")
    await redis_client.exists("test_key")
    await redis_client.delete("test_key")

    await redis_client.close()

# Запуск примера (если скрипт выполняется напрямую)
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
