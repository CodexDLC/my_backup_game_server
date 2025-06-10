# Logic/ApplicationLogic/tick_infra/tick_utils/task_utils.py

from typing import Dict, Any, List

# --- НОВЫЕ ИМПОРТЫ ---
# Импортируем высокоуровневый менеджер для работы с задачами и константы
from game_server.Logic.InfrastructureLogic.app_cache.services import task_queue_cache_manager
from game_server.Logic.InfrastructureLogic.app_cache import central_redis_constants as constants
from game_server.Logic.InfrastructureLogic.app_cache import central_redis_client

# --- КОММЕНТАРИЙ ---
# Обрати внимание: мы больше не импортируем `redis.asyncio` и не передаем `redis_client` в каждую функцию.
# Функции теперь напрямую используют импортированный менеджер.


async def set_tick_status(key: str, value: str):
    """Устанавливает статус конкретного компонента тика."""
    # Было: await redis_client.hset("tick_status", key, value)
    # Стало: Используем метод менеджера, который инкапсулирует эту логику.
    await task_queue_cache_manager.set_tick_status(key, value)


async def get_tick_status(key: str) -> str | None:
    """Получает статус конкретного компонента тика."""
    # Было: await redis_client.hget("tick_status", key)
    return await task_queue_cache_manager.get_tick_status(key)


async def get_start_time() -> str | None:
    """Получает время запуска сервера."""
    # Было: await redis_client.get("server_start_time")
    return await task_queue_cache_manager.get_server_start_time()


async def get_processing_queue() -> list:
    """Получает все элементы из очереди обработки тиков."""
    # Было: await redis_client.lrange("tick_processing_queue", 0, -1)
    # Стало: Используем менеджер и константу для имени очереди.
    return await task_queue_cache_manager.get_tasks_from_queue(constants.TICK_PROCESSING_QUEUE)


async def add_processed_batch(batch_id: str, data: Dict[str, Any]):
    """Добавляет информацию об обработанном батче."""
    # Было: await redis_client.hset("processed_batches", batch_id, json.dumps(data))
    await task_queue_cache_manager.add_processed_batch_info(batch_id, data)


async def remove_processed_batch(batch_id: str):
    """Удаляет информацию об обработанном батче."""
    # Было: await redis_client.hdel("processed_batches", batch_id)
    await task_queue_cache_manager.remove_processed_batch_info(batch_id)


async def get_processed_batches() -> List[str]:
    """Получает ID всех обработанных батчей."""
    # Было: await redis_client.hkeys("processed_batches")
    return await task_queue_cache_manager.get_all_processed_batch_ids()


async def get_batch_status_from_redis(batch_id: str) -> Dict[str, Any]:
    """Получает полный статус батча по его ID."""
    # Было: await redis_client.hgetall(f"batch_status:{batch_id}")
    # Стало: Менеджер сам формирует ключ и извлекает данные.
    return await task_queue_cache_manager.get_batch_status(batch_id)


async def delete_keys(keys: List[str]):
    """
    Удаляет ключи напрямую.
    Эта функция является примером допустимого низкоуровневого действия,
    когда нет подходящего метода в менеджере.
    """
    if keys:
        # Было: await redis_client.delete(*keys)
        # Стало: Используем центральный клиент для общих операций.
        await central_redis_client.delete(*keys)