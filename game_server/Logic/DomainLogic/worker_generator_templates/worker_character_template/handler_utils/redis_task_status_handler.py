import logging
from typing import List, Dict, Any, Tuple, Optional

# 🔥 ДОБАВЛЕНО: Импорт класса для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from game_server.config.constants.redis import CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


# 🔥 ИЗМЕНЕНИЕ: Функция теперь принимает task_queue_cache_manager
async def get_task_specs_from_redis(
    batch_id: str,
    task_key_template: str,
    task_queue_cache_manager: TaskQueueCacheManager, # 🔥 ДОБАВЛЕНО
) -> Tuple[Optional[List[Dict[str, Any]]], int, Optional[str]]:
    """
    Извлекает спецификации задачи и целевое количество через TaskQueueCacheManager.
    """
    log_prefix = f"CHAR_SPEC_GET({batch_id}):"
    # 🔥 ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ task_queue_cache_manager
    loaded_data = await task_queue_cache_manager.get_character_task_specs(
        batch_id=batch_id,
        key_template=task_key_template
    )
    
    specs, target_count, error_message = loaded_data

    if error_message:
        logger.error(f"{log_prefix} Ошибка при получении спецификаций: {error_message}")
    
    return specs, target_count, error_message


# 🔥 ИЗМЕНЕНИЕ: Функция теперь принимает task_queue_cache_manager (если не было добавлено ранее)
async def update_task_generated_count(
    batch_id: str,
    task_key_template: str,
    task_queue_cache_manager: TaskQueueCacheManager, # 🔥 ДОБАВЛЕНО
    increment_by: int = 1
) -> Optional[int]:
    """Атомарно инкрементирует 'generated_count_in_chunk' через TaskQueueCacheManager."""
    log_prefix = f"CHAR_COUNT_UPDATE({batch_id}):"
    # 🔥 ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ task_queue_cache_manager
    new_count = await task_queue_cache_manager.increment_task_generated_count(
        batch_id=batch_id,
        key_template=task_key_template,
        increment_by=increment_by
    )
    if new_count is not None:
        logger.debug(f"{log_prefix} Счетчик сгенерированных элементов для задачи '{batch_id}' обновлен до {new_count}.")
    else:
        logger.warning(f"{log_prefix} Не удалось обновить счетчик сгенерированных элементов для задачи '{batch_id}'.")
    return new_count

# 🔥 ИЗМЕНЕНИЕ: Функция теперь принимает task_queue_cache_manager (если не было добавлено ранее)
async def set_task_final_status(
    batch_id: str,
    task_key_template: str,
    status: str,
    task_queue_cache_manager: TaskQueueCacheManager, # 🔥 ДОБАВЛЕНО
    final_generated_count: Optional[int] = None,
    target_count: Optional[int] = None,
    error_message: Optional[str] = None,
    was_empty: bool = False
) -> None:
    """Устанавливает финальный статус задачи через TaskQueueCacheManager."""
    log_prefix = f"CHAR_FINAL_STATUS({batch_id}):"
    # 🔥 ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ task_queue_cache_manager
    await task_queue_cache_manager.set_character_task_final_status(
        batch_id=batch_id,
        key_template=task_key_template,
        status=status,
        final_generated_count=final_generated_count,
        target_count=target_count,
        error_message=error_message,
        was_empty=was_empty
    )
    logger.info(f"{log_prefix} Финальный статус задачи '{batch_id}' установлен на '{status}'.")