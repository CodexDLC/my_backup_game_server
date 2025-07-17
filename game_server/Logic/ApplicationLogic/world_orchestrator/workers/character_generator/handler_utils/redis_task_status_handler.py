# game_server/Logic/DomainLogic/worker_generator_templates/worker_character_template/handler_utils/redis_task_status_handler.py

import logging
from typing import List, Dict, Any, Tuple, Optional

from game_server.config.logging.logging_setup import app_logger as logger
# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore


async def get_task_specs_from_redis(
    batch_id: str,
    task_key_template: str,
    redis_batch_store: RedisBatchStore, # <<< ИЗМЕНЕНО
) -> Tuple[Optional[List[Dict[str, Any]]], int, Optional[str]]:
    """
    Извлекает спецификации задачи и целевое количество через RedisBatchStore.
    """
    log_prefix = f"CHAR_SPEC_GET({batch_id}):"
    try:
        # <<< ИЗМЕНЕНО: Используем redis_batch_store.load_batch
        loaded_data = await redis_batch_store.load_batch(
            batch_id=batch_id,
            key_template=task_key_template
        )
        
        if not loaded_data:
            logger.error(f"{log_prefix} Не удалось загрузить данные батча.")
            return None, 0, "Batch data not found in Redis."

        specs = loaded_data.get("specs")
        target_count = loaded_data.get("target_count", 0)
        
        if not specs:
            logger.warning(f"{log_prefix} Данные батча загружены, но не содержат спецификаций ('specs').")
            return None, target_count, "Specs not found in batch data."

        return specs, target_count, None

    except Exception as e:
        logger.critical(f"{log_prefix} Ошибка при получении спецификаций батча: {e}", exc_info=True)
        return None, 0, str(e)


# <<< УДАЛЕНО: Функция update_task_generated_count больше не нужна.
# Обновление счетчика происходит один раз в конце через set_task_final_status.


async def set_task_final_status(
    batch_id: str,
    task_key_template: str,
    status: str,
    redis_batch_store: RedisBatchStore, # <<< ИЗМЕНЕНО
    final_generated_count: Optional[int] = None,
    target_count: Optional[int] = None,
    error_message: Optional[str] = None,
    was_empty: bool = False
) -> None:
    """Устанавливает финальный статус задачи через RedisBatchStore."""
    log_prefix = f"CHAR_FINAL_STATUS({batch_id}):"
    
    fields_to_update = {"status": status}
    if final_generated_count is not None:
        fields_to_update["final_generated_count"] = final_generated_count
    if target_count is not None:
        fields_to_update["target_count"] = target_count
    if error_message:
        fields_to_update["error_message"] = error_message
    if was_empty:
        fields_to_update["was_empty"] = True

    try:
        # <<< ИЗМЕНЕНО: Используем redis_batch_store.update_fields
        await redis_batch_store.update_fields(
            batch_id=batch_id,
            key_template=task_key_template,
            fields=fields_to_update
        )
        logger.info(f"{log_prefix} Финальный статус задачи '{batch_id}' установлен на '{status}'.")
    except Exception as e:
        logger.error(f"{log_prefix} Ошибка при установке финального статуса задачи '{batch_id}': {e}", exc_info=True)

