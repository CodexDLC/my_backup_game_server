import random
from fastapi import APIRouter, HTTPException
import redis.asyncio as aioredis  # Исправленный импорт

router = APIRouter()

# Настройка подключения к Redis
async def get_redis():
    return aioredis.Redis.from_url("redis://localhost", decode_responses=True)

@router.get("/generate_pool", summary="Сгенерировать пул чисел до 65,000")
async def generate_pool():
    redis = await get_redis()
    # Генерируем числа от 1 до 65,000 и добавляем их в Redis
    for num in range(1, 65001):
        await redis.set(f"number:{num}", num)  # Сохраняем в Redis

    return {"message": "Пул чисел успешно сгенерирован"}

@router.get("/next_random", summary="Получить следующее случайное число из пула")
async def get_next_random():
    redis = await get_redis()
    # Получаем случайное число из Redis
    random_number = random.randint(1, 65000)  # Генерируем случайное число
    number = await redis.get(f"number:{random_number}")

    if not number:
        raise HTTPException(status_code=404, detail="Число не найдено")

    return {"random_number": number}
