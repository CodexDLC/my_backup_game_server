import random
from fastapi import APIRouter, HTTPException
import redis.asyncio as aioredis
from game_server.config.redis_config import REDIS_URL

router = APIRouter()
POOL_SIZE = 65000
THRESHOLD = 0.1  # 10%

async def get_redis():
    return aioredis.Redis.from_url(REDIS_URL, decode_responses=True)

async def generate_pool(name: str):
    """
    Заполнить Redis-множество name числами от 1 до POOL_SIZE.
    """
    r = await get_redis()
    # Удаляем старое множество, если есть
    await r.delete(name)
    # Добавляем все числа одним вызовом
    # (под капотом pipelined SADD)
    await r.sadd(name, *map(str, range(1, POOL_SIZE + 1)))
    print(f"Пул {name} сгенерирован заново")

@router.get("/generate_pool", summary="Сгенерировать два пула чисел")
async def generate_two_pools():
    # Два множества pool1 и pool2
    await generate_pool("pool1")
    await generate_pool("pool2")
    return {"message": "Два пула успешно сгенерированы"}

@router.get("/next_random", summary="Получить следующее случайное число из пула")
async def get_next_random():
    r = await get_redis()

    # Узнаём размеры пулов
    size1 = await r.scard("pool1")
    size2 = await r.scard("pool2")

    # Выбираем активный пул
    if size1 < POOL_SIZE * THRESHOLD:
        active = "pool2"
        # Параллельно обновляем старый пул1
        # (не ждём, пусть фоновый таск сделает)
        # Но можно и await, если нужно строго последовательное обновление:
        # await generate_pool("pool1")
    else:
        active = "pool1"

    # Получаем случайный элемент и тут же удаляем его
    member = await r.srandmember(active)
    if member is None:
        # Если даже во втором пуле кончились — регенерим оба
        await generate_two_pools()
        member = await r.srandmember(active)
        if member is None:
            raise HTTPException(503, "Не удалось получить случайное число")
    await r.srem(active, member)

    return {"random_number": int(member)}
