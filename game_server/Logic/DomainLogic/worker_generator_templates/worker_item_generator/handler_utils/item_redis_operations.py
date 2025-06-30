# game_server/Logic/DomainLogic/worker_generator_templates/worker_item_template/handler_utils/item_redis_operations.py

import logging
from typing import Optional

from game_server.config.logging.logging_setup import app_logger as logger
# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore


# <<< УДАЛЕНО: Функция get_batch_specs_from_redis больше не нужна.
# Загрузка данных батча теперь происходит на уровне основной ARQ-задачи,
# которая затем передает готовые спецификации в ItemBatchProcessor.


async def update_redis_task_status(
    redis_worker_batch_id: str,
    task_key_template: str,
    status: str,
    log_prefix: str,
    redis_batch_store: RedisBatchStore,  # <<< ИЗМЕНЕНО: Принимаем RedisBatchStore
    error_message: Optional[str] = None,
    ttl_seconds_on_completion: Optional[int] = None,
    final_generated_count: Optional[int] = None
) -> None:
    """
    Обновляет статус задачи в Redis через RedisBatchStore.
    """
    fields_to_update = {"status": status}
    if error_message:
        fields_to_update['error_message'] = error_message
    
    if final_generated_count is not None:
        fields_to_update['final_generated_count'] = final_generated_count

    try:
        # <<< ИЗМЕНЕНО: Используем метод update_fields из RedisBatchStore
        await redis_batch_store.update_fields(
            batch_id=redis_worker_batch_id,
            key_template=task_key_template,
            fields=fields_to_update,
            ttl_seconds=ttl_seconds_on_completion
        )
        logger.debug(f"{log_prefix} Статус задачи '{redis_worker_batch_id}' обновлен на '{status}' в Redis.")
    except Exception as e:
        logger.error(f"{log_prefix} Ошибка при обновлении статуса задачи '{redis_worker_batch_id}' в Redis: {e}", exc_info=True)

