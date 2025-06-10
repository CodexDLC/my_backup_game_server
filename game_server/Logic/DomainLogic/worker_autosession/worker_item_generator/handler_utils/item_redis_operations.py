import json
from typing import List, Dict, Any, Optional
from game_server.services.logging.logging_setup import logger

# 🔥 УДАЛЕНО: Импорт CentralRedisClient здесь больше не нужен, так как он не передается вниз
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

# Импортируем ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР task_queue_cache_manager
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue_cache_manager import task_queue_cache_manager


async def get_batch_specs_from_redis(
    redis_worker_batch_id: str,
    task_key_template: str,
    log_prefix: str,
    # 🔥 ИСПРАВЛЕНИЕ: Удаляем redis_client из аргументов функции
    # redis_client: CentralRedisClient
) -> Optional[List[Dict[str, Any]]]:
    """
    Получает спецификации батча из Redis через TaskQueueCacheManager.
    Менеджер сам управляет своим подключением к Redis.
    """
    return await task_queue_cache_manager.get_task_batch_specs(
        batch_id=redis_worker_batch_id,
        key_template=task_key_template,
        log_prefix=log_prefix,
        # 🔥 ИСПРАВЛЕНИЕ: Удаляем передачу redis_client_instance
        # redis_client_instance=redis_client
    )


async def update_redis_task_status(
    redis_worker_batch_id: str,
    task_key_template: str,
    status: str,
    log_prefix: str,
    # 🔥 ИСПРАВЛЕНИЕ: Удаляем redis_client из аргументов функции
    # redis_client: CentralRedisClient,
    error_message: Optional[str] = None,
    ttl_seconds_on_completion: Optional[int] = None
) -> None:
    """
    Обновляет статус задачи в Redis через TaskQueueCacheManager.
    Менеджер сам управляет своим подключением к Redis.
    """
    await task_queue_cache_manager.update_task_status(
        batch_id=redis_worker_batch_id,
        key_template=task_key_template,
        status=status,
        log_prefix=log_prefix,
        error_message=error_message,
        ttl_seconds=ttl_seconds_on_completion,
        # 🔥 ИСПРАВЛЕНИЕ: Удаляем передачу redis_client_instance
        # redis_client_instance=redis_client
    )