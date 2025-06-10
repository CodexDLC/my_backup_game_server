import asyncio
from datetime import datetime

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient


class RandomPoolManager:
    _instance = None
    redis_prefix = "random_pool:"

    max_range = 10_000  # Основной диапазон
    factor = 10         # Количество повторений
    
    pool_size = max_range * factor  # Автоматический расчёт размера пула
    

    def __new__(cls, *args, **kwargs):
        # При первом вызове создаём экземпляр,
        # при последующих возвращаем уже созданный объект.
        if cls._instance is None:
            cls._instance = super(RandomPoolManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, redis=None):
        # Чтобы повторный вызов конструктора не переинициализировал объект,
        # добавляем флаг инициализации.
        if not hasattr(self, "_initialized"):
            if redis is None:
                # Если подключение не передали, создаем его сами.
                self.redis = CentralRedisClient().redis
            else:
                self.redis = redis
            self._initialized = True

    async def init_redis(self):
        """Проверяет, что соединение с Redis установлено."""
        try:
            pong = await self.redis.ping()
        except Exception as e:
            print(f"Ошибка при подключении к Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")
        
        if not pong:
            raise ConnectionError("❌ Redis недоступен!")
        
        return self.redis

    async def init_pool(self) -> None:
        """Инициализация пула: динамически по заданным параметрам"""
        await self.init_redis()
        await self.redis.delete(f"{self.redis_prefix}main")

        chunk_size = self.max_range // 10  # Разделяем на 10 частей

        async with self.redis.pipeline() as pipe:
            for chunk in range(1, self.max_range + 1, chunk_size):  # Используем переменные
                pipe.sadd(
                    f"{self.redis_prefix}main",
                    *range(chunk, min(chunk + chunk_size, self.max_range + 1))  # Динамически загружаем
                )
            await pipe.execute()

        await self.redis.hset(f"{self.redis_prefix}meta", mapping={
            "pool_size": self.pool_size,  # Используем переменную
            "range_max": self.max_range,  # Используем переменную
            "updated_at": datetime.now().isoformat()
        })


    async def check_chance(self, chance: float) -> bool:
        """
        Проверяет срабатывание шанса.
        :param chance: Вероятность от 0.00001 до 1.0
        :return: True, если шанс сработал.
        """
        if not 0.00001 <= chance <= 1.0:
            raise ValueError("Шанс должен быть между 0.00001 и 1.0")
            
        await self.init_redis()

        # Привязываем к max_range, а не к pool_size
        max_num = round(self.max_range * chance)
        if max_num < 1:
            max_num = 1

        # Получаем случайное число из пула
        num = await self.redis.spop(f"{self.redis_prefix}main")
        
        # Если пула нет, пополняем его и снова пробуем взять число
        if num is None:
            print("⚠️ Пул закончился! Пополняем...")
            await self.init_pool()
            num = await self.redis.spop(f"{self.redis_prefix}main")

        # Проверяем, входит ли число в заданный шанс
        return int(num) <= max_num if num is not None else False


    async def get_stats(self) -> dict:
        """Возвращает статистику по пулу чисел."""
        await self.init_redis()
        remaining = await self.redis.scard(f"{self.redis_prefix}main")
        return {
            "total_numbers": self.pool_size,
            "remaining_numbers": remaining,
            "used_numbers": self.pool_size - remaining,
            "min_chance": "0.00001%",
            "updated_at": (await self.redis.hget(f"{self.redis_prefix}meta", "updated_at")).decode()
        }
    
    async def create_pool_by_key(self, key: str, pool_size: int = None) -> None:
        """
        Создаёт отдельный пул чисел под заданный ключ и сразу добавляет возможность проверки шанса.
        :param key: уникальный ключ пула (например, dungeon_id или box_type)
        :param pool_size: размер пула, по умолчанию self.pool_size
        """
        await self.init_redis()
        size = pool_size or (self.max_range * self.factor)  # Автокоррекция размера
        pool_key = f"{self.redis_prefix}{key}"

        await self.redis.delete(pool_key)
        chunk_size = max(10_000, self.max_range // 10)  # Динамическое дробление

        async with self.redis.pipeline() as pipe:
            for chunk in range(1, self.max_range + 1, chunk_size):
                pipe.sadd(pool_key, *range(chunk, min(chunk + chunk_size, self.max_range + 1)))
            await pipe.execute()

        await self.redis.hset(f"{pool_key}:meta", mapping={
            "pool_size": size,
            "max_range": self.max_range,
            "created_at": datetime.now().isoformat()
        })
        
    async def check_chance_by_key(self, key: str, chance: float) -> bool:
        """
        Проверяет шанс по пулу, привязанному к ключу.
        :param key: ключ пула
        :param chance: от 0.00001 до 1.0
        :return: True, если шанс сработал.
        """
        if not 0.00001 <= chance <= 1.0:
            raise ValueError("Шанс должен быть между 0.00001 и 1.0")

        await self.init_redis()
        pool_key = f"{self.redis_prefix}{key}"

        # Получаем `pool_size`, если нет — устанавливаем стандартное значение
        size_raw = await self.redis.hget(f"{pool_key}:meta", "pool_size")
        size = int(size_raw.decode()) if size_raw else self.pool_size

        # Привязываем `max_num` к `max_range`, а не к `pool_size`
        max_num = max(1, round(self.max_range * chance))

        # Получаем случайное число
        num_raw = await self.redis.spop(pool_key)
        num = int(num_raw.decode()) if num_raw else None

        # Если пул пуст, пересоздаём его
        if num is None:
            print(f"⚠️ Пул `{key}` закончился, пополняем!")
            await self.create_pool_by_key(key, size)
            num_raw = await self.redis.spop(pool_key)
            num = int(num_raw.decode()) if num_raw else None

        return num is not None and num <= max_num

    
    async def clear_pool(self, key: str = None) -> None:
        """
        Очищает основной пул (`main`) или пул по заданному ключу.
        :param key: уникальный ключ пула (если None, удаляет `main`).
        """
        r = await self.init_redis()
        
        if key:
            # Очищаем пул с конкретным ключом
            pool_key = f"{self.redis_prefix}{key}"
            await r.delete(pool_key)
            await r.delete(f"{pool_key}:meta")
            print(f"✅ Пул `{key}` успешно очищен!")
        else:
            # Очищаем основной пул (`main`)
            await r.delete(f"{self.redis_prefix}main")
            await r.delete(f"{self.redis_prefix}meta")
            print("✅ Основной пул (`main`) очищен!")
            

    async def get_random_number(self, key: str = "main") -> int:
        """
        Возвращает одно случайное число из указанного пула в Redis.
        Если пул пуст, автоматически пополняет его.
        :param key: Ключ пула (например, "main" или "character_rarity_selection_pool").
        :return: Случайное число из пула.
        """
        await self.init_redis()
        pool_key = f"{self.redis_prefix}{key}"

        num_raw = await self.redis.spop(pool_key)
        num = int(num_raw.decode()) if num_raw else None

        if num is None:
            print(f"⚠️ Пул `{key}` закончился, пополняем!")
            # Используем max_range из meta, если есть, или из self.max_range
            meta = await self.redis.hgetall(f"{pool_key}:meta")
            current_max_range = int(meta.get(b"max_range", self.max_range)) if meta else self.max_range
            current_pool_size = int(meta.get(b"pool_size", self.pool_size)) if meta else self.pool_size

            # Важно: create_pool_by_key должен использовать переданные параметры или свои дефолты
            await self.create_pool_by_key(key, pool_size=current_pool_size) # Или пересоздать с актуальными параметрами
            
            num_raw = await self.redis.spop(pool_key)
            num = int(num_raw.decode()) if num_raw else None
        
        if num is None:
            raise RuntimeError(f"Не удалось получить число из пула `{key}` даже после пополнения.")

        return num

    
