import json
import logging
from typing import List, Dict, Any, Optional

# 🔥 ДОБАВЛЕНО: Импорт класса для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Убедимся, что logger импортирован


# 🔥 ИЗМЕНЕНИЕ: Функция теперь принимает task_queue_cache_manager как аргумент
async def get_batch_specs_from_redis(
    redis_worker_batch_id: str,
    task_key_template: str,
    log_prefix: str,
    task_queue_cache_manager: TaskQueueCacheManager # 🔥 ДОБАВЛЕНО: Принимаем менеджер задач
) -> Optional[List[Dict[str, Any]]]:
    """
    Получает спецификации батча из Redis через TaskQueueCacheManager.
    Менеджер сам управляет своим подключением к Redis.
    """
    logger.debug(f"{log_prefix} Запрос спецификаций батча '{redis_worker_batch_id}' из Redis.")
    try:
        # 🔥 ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ task_queue_cache_manager
        batch_specs = await task_queue_cache_manager.get_task_batch_specs(
            batch_id=redis_worker_batch_id,
            key_template=task_key_template,
            log_prefix=log_prefix,
        )
        if batch_specs:
            logger.info(f"{log_prefix} Получено {len(batch_specs)} спецификаций из Redis для батча '{redis_worker_batch_id}'.")
            return batch_specs
        else:
            logger.warning(f"{log_prefix} Не удалось получить спецификации батча '{redis_worker_batch_id}' из Redis.")
            return None
    except Exception as e:
        logger.critical(f"{log_prefix} ОБНАРУЖЕНА ОШИБКА при получении спецификаций батча: {e}", exc_info=True)
        return None


# 🔥 ИЗМЕНЕНИЕ: Обновляем сигнатуру функции update_redis_task_status
async def update_redis_task_status(
    redis_worker_batch_id: str,
    task_key_template: str,
    status: str,
    log_prefix: str,
    task_queue_cache_manager: TaskQueueCacheManager, # 🔥 ДОБАВЛЕНО: Принимаем менеджер задач
    error_message: Optional[str] = None,
    ttl_seconds_on_completion: Optional[int] = None,
    final_generated_count: Optional[int] = None # 🔥🔥🔥 ДОБАВЛЕНО: Новый аргумент, который вызывал ошибку
) -> None:
    """
    Обновляет статус задачи в Redis через TaskQueueCacheManager.
    Менеджер сам управляет своим подключением к Redis.
    """
    kwargs = {}
    if error_message:
        kwargs['error_message'] = error_message
    
    # ttl_seconds_on_completion будет передан в update_task_status как ttl_seconds
    if ttl_seconds_on_completion is not None:
        kwargs['ttl_seconds'] = ttl_seconds_on_completion

    # 🔥🔥🔥 ДОБАВЛЕНО: Передача final_generated_count в update_task_status менеджера
    if final_generated_count is not None:
        kwargs['final_generated_count'] = final_generated_count

    try:
        # 🔥 ИСПОЛЬЗУЕМ ПЕРЕДАННЫЙ task_queue_cache_manager
        await task_queue_cache_manager.update_task_status(
            batch_id=redis_worker_batch_id,
            key_template=task_key_template,
            status=status,
            log_prefix=log_prefix,
            **kwargs
        )
        logger.debug(f"{log_prefix} Статус задачи '{redis_worker_batch_id}' обновлен на '{status}' в Redis.")
    except Exception as e:
        logger.error(f"{log_prefix} Ошибка при обновлении статуса задачи '{redis_worker_batch_id}' в Redis: {e}", exc_info=True)