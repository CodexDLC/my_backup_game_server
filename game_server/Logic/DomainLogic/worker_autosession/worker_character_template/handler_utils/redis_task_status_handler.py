# Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/redis_task_status_handler.py

from typing import List, Dict, Any, Tuple, Optional

# --- Логгер ---
from game_server.services.logging.logging_setup import logger

# --- ИСПРАВЛЕННЫЙ ИМПОРТ ---
# Убираем ненужный импорт CentralRedisClient
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# Импортируем наш готовый глобальный экземпляр менеджера
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue_cache_manager import task_queue_cache_manager


# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ---
# Убираем redis_client из аргументов
async def get_task_specs_from_redis(
    batch_id: str,
    task_key_template: str,
) -> Tuple[Optional[List[Dict[str, Any]]], int, Optional[str]]:
    """
    Извлекает спецификации задачи и целевое количество через TaskQueueCacheManager.
    """
    # Вызов становится чистым, без лишних аргументов.
    # Менеджер сам использует свой внутренний redis-клиент.
    return await task_queue_cache_manager.get_character_task_specs(
        batch_id=batch_id,
        key_template=task_key_template
    )


# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ---
async def update_task_generated_count(
    batch_id: str,
    task_key_template: str,
    increment_by: int = 1
) -> Optional[int]:
    """Атомарно инкрементирует 'generated_count_in_chunk' через TaskQueueCacheManager."""
    # Вызов становится чистым
    return await task_queue_cache_manager.increment_task_generated_count(
        batch_id=batch_id,
        key_template=task_key_template,
        increment_by=increment_by
    )

# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ---
async def set_task_final_status(
    batch_id: str,
    task_key_template: str,
    status: str,
    final_generated_count: Optional[int] = None,
    target_count: Optional[int] = None,
    error_message: Optional[str] = None,
    was_empty: bool = False
) -> None:
    """Устанавливает финальный статус задачи через TaskQueueCacheManager."""
    # Вызов становится чистым
    await task_queue_cache_manager.set_character_task_final_status(
        batch_id=batch_id,
        key_template=task_key_template,
        status=status,
        final_generated_count=final_generated_count,
        target_count=target_count,
        error_message=error_message,
        was_empty=was_empty
    )
