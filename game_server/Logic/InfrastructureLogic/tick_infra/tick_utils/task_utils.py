import asyncio
from datetime import datetime, timezone
import json
import time
from typing import Awaitable
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger



# ✅ Работа со статусами задач

async def set_tick_status(redis_client, character_id, tick_id, status):
    """Обновляет статус задачи в `tick_status`."""
    tick_key = f"tick_status_{character_id}_{tick_id}"
    await redis_client.hset("tick_status", tick_key, status)
    logger.info(f"✅ `tick_status` обновлён: {tick_key} → {status}")

async def get_tick_status(redis_client, character_id, tick_id):
    """Получает статус задачи из `tick_status`."""
    tick_key = f"tick_status_{character_id}_{tick_id}"
    flag = await redis_client.hget("tick_status", tick_key)
    return flag if flag else None


# ✅ Проверка доступных задач

async def check_for_available_batches(redis_client):
    """Проверяет, есть ли доступные задачи, и возвращает `True` или `False`."""
    logger.debug("🔄 [DEBUG] Запрос `available_workers_cache` из Redis...")
    available_workers_raw = await redis_client.get("available_workers_cache") or "[]"
    available_workers = json.loads(available_workers_raw)

    if not available_workers:
        logger.info("✅ Нет доступных задач.")
        return False

    logger.debug(f"📦 [DEBUG] Доступные задачи: {available_workers}")
    return True


async def check_for_initiation_batches(redis_client):
    """Проверяет, есть ли `batch_id` со статусом `initiation` в `batch_status`."""
    logger.debug("🔄 [DEBUG] Запрос `batch_status` из Redis...")
    batch_statuses_raw = await redis_client.hgetall("batch_status")

    if not batch_statuses_raw:
        logger.info("✅ `batch_status` пуст, нет активных `batch_id`.")
        return False  

    logger.debug(f"📦 [DEBUG] Проверяем статусы `batch_id`: {batch_statuses_raw}")

    for batch_id, status in batch_statuses_raw.items():
        if status == "initiation":
            logger.info(f"✅ Найден `batch_id={batch_id}` со статусом `initiation`, запускаем обработку!")
            return True  

    logger.info("⚠ Нет `batch_id` со статусом `initiation`, обработка не требуется.")
    return False  


# ✅ Инициализация сервера

async def initialize_server(redis_client):
    """Генерирует `server_start_time` и сохраняет в Redis при каждом рестарте."""
    server_start_time = int(time.time())  
    await redis_client.set("server_start_time", server_start_time)
    
    logger.info(f"🕒 [INIT] Обновили `server_start_time`: {server_start_time}")
    
    return server_start_time


# ✅ Ожидание завершения задач

async def finish_active_tasks(redis_client):
    """Ожидает завершения всех активных задач перед остановкой сервиса."""
    while True:
        active_handlers = await redis_client.hgetall("active_handlers")
        
        if not active_handlers:
            logger.info("✅ Все задачи завершены, завершаем систему...")
            break

        logger.info(f"⏳ Ожидание завершения {len(active_handlers)} активных задач...")
    
        await asyncio.sleep(1)  


# ✅ Проверка `tick_processing_queue`

async def check_tick_processing_queue(redis_client):
    """Проверяет `tick_processing_queue` и возвращает `True`, если есть хотя бы одна задача со статусом 'I'."""
    raw_tasks = await redis_client.lrange("tick_processing_queue", 0, -1)  

    if not raw_tasks:
        logger.info("💤 `tick_processing_queue` пуст, работы нет.")
        return False  

    logger.info(f"🔄 Найдено `{len(raw_tasks)}` задач в `tick_processing_queue`.")

    for task in raw_tasks:
        task_parts = task.split(":")
        if len(task_parts) < 3:
            logger.warning(f"⚠ Ошибка формата задачи: `{task}`. Пропускаем.")
            continue

        status_key = f"tick_status_{task_parts[1]}_{task_parts[2]}"  
        status = await redis_client.hget("tick_status", status_key)

        if status == "I":
            logger.info(f"✅ Найдена задача `{task}` со статусом 'I'. Можно запускать обработку!")
            return True  

    logger.info("⚠ Все задачи не новые (`I`). Нет работы.")
    return False  


async def get_tick_tasks(redis_client):
    """Получает все задачи из очереди `tick_processing_queue`."""
    tasks = await redis_client.lrange("tick_processing_queue", 0, -1)  # Получаем все задачи из очереди
    return tasks  # Возвращаем список задач


async def set_status_coordinator(self, status_name: str, value: bool):
    val_str = "true" if value else "false"
    key = f"coordinator:{status_name}"
    await self.redis.set(key, val_str)


async def check_and_run(
    db,  # Объект БД с методом get_data()
    collector_runner: Awaitable  # Функция для запуска Collector (принимает tick_id)
) -> bool:
    """Проверяет auto_sessions и запускает Collector при необходимости.
    
    Returns:
        bool: Была ли работа (True = Collector запущен)
    """
    logger.debug("🔎 Проверка auto_sessions...")
    
    current_time = datetime.now(timezone.utc)
    query = "SELECT next_tick_at FROM auto_sessions"
    result = await db.get_data(query)

    if not any(row["next_tick_at"] <= current_time for row in result):
        logger.debug("✅ Нет активных задач")
        return False

    logger.debug("🔍 Найдена работа! Запускаем Collector...")
    tick_id = int(current_time.timestamp())
    await collector_runner(tick_id)  # Например: `Collector().lifecycle()`
    return True