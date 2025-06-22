import logging
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod # Добавлено

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.settings.redis_setting import DEFAULT_TTL_TASK_STATUS

# Обновленный импорт RedisBatchStore (теперь в той же папке)
from .redis_batch_store import RedisBatchStore # Изменено

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Изменено

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager # Добавлено

# Изменяем класс TaskQueueCacheManager, чтобы он наследовал от ITaskQueueCacheManager
class TaskQueueCacheManager(ITaskQueueCacheManager): # Изменено
    """
    Высокоуровневый менеджер для кэширования и управления задачами и их статусами в Redis.
    Использует RedisBatchStore для низкоуровневых операций с батчами.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis_batch_store = RedisBatchStore(redis_client)
        self.logger = logger # Используем app_logger
        logger.info("✅ TaskQueueCacheManager инициализирован.")

    async def add_task_to_queue(self, batch_id: str, key_template: str, specs: List[Dict[str, Any]],
                                 target_count: int, initial_status: str = "pending") -> bool:
        redis_task_key = key_template.format(batch_id=batch_id)
        task_data = {
            "specs": specs,
            "status": initial_status,
            "target_count_in_chunk": target_count,
            "generated_count_in_chunk": 0,
            "timestamp": int(time.time())
        }

        success = await self.redis_batch_store.save_batch(
            key_template=key_template,
            batch_id=batch_id,
            batch_data=task_data,
            ttl_seconds=DEFAULT_TTL_TASK_STATUS
        )

        if success:
            self.logger.info(f"💾 Задача '{batch_id}' с {len(specs)} спецификациями добавлена в очередь Redis (через RedisBatchStore).")
            await self.update_task_status(
                batch_id=batch_id, key_template=key_template, status=initial_status, log_prefix=f"TASK({batch_id}):"
            )
            return True
        else:
            self.logger.error(f"❌ Ошибка: RedisBatchStore.save_batch вернул False для батча '{batch_id}'.")
            return False

    async def get_task_batch_specs(self, batch_id: str, key_template: str, log_prefix: str) -> Optional[List[Dict[str, Any]]]:
        loaded_data = await self.redis_batch_store.load_batch(key_template=key_template, batch_id=batch_id)

        if not loaded_data:
            self.logger.error(f"{log_prefix} Задачи с ID {batch_id} (ключ: {key_template.format(batch_id=batch_id)}) не найдена в Redis (через RedisBatchStore).")
            await self.update_task_status(
                batch_id=batch_id, key_template=key_template, status="failed",
                log_prefix=log_prefix, error_message="Batch specs not found (via RedisBatchStore)"
            )
            return None

        specs_obj = loaded_data.get('specs')
        target_count = loaded_data.get('target_count_in_chunk', 0)

        if specs_obj is None:
            self.logger.error(f"{log_prefix} Отсутствует 'specs' в задаче {batch_id}.")
            await self.update_task_status(
                batch_id=batch_id, key_template=key_template, status="failed",
                log_prefix=log_prefix, error_message="Missing specs"
            )
            return None

        batch_specs = specs_obj
        self.logger.info(f"{log_prefix} Получено {len(batch_specs)} спецификаций (через RedisBatchStore).")

        await self.update_task_status(
            batch_id=batch_id, key_template=key_template,
            status="in_progress", log_prefix=log_prefix
        )
        return batch_specs

    async def update_task_status(self, batch_id: str, key_template: str, status: str, log_prefix: str,
                                 error_message: Optional[str] = None, ttl_seconds: Optional[int] = None,
                                 final_generated_count: Optional[int] = None) -> None:
        fields_to_update = {"status": status}
        if error_message:
            fields_to_update["error_message"] = error_message

        if final_generated_count is not None:
            fields_to_update["generated_count_in_chunk"] = final_generated_count

        final_ttl = ttl_seconds if ttl_seconds is not None else DEFAULT_TTL_TASK_STATUS

        await self.redis_batch_store.update_fields(
            key_template=key_template,
            batch_id=batch_id,
            fields=fields_to_update,
            ttl_seconds=final_ttl if status in ["completed", "completed_with_warnings", "failed"] else None
        )
        self.logger.info(f"{log_prefix} Статус задачи '{batch_id}' обновлен на '{status}' (через RedisBatchStore).")

    async def get_character_task_specs(self, batch_id: str, key_template: str) -> Tuple[Optional[List], int, Optional[str]]:
        log_prefix = f"CHAR_SPEC_GET({batch_id}):"
        loaded_data = await self.redis_batch_store.load_batch(key_template=key_template, batch_id=batch_id)

        if not loaded_data:
            return None, 0, f"Задача с ключом {key_template.format(batch_id=batch_id)} не найдена (через RedisBatchStore)."

        specs_obj = loaded_data.get('specs')
        target_count = loaded_data.get('target_count_in_chunk', 0)

        if specs_obj is None:
            error_msg = f"Отсутствует 'specs' в задаче {key_template.format(batch_id=batch_id)} (через RedisBatchStore)."
            await self.set_character_task_final_status(
                batch_id=batch_id, key_template=key_template,
                status="failed", error_message=error_msg
            )
            return None, target_count, error_msg

        return specs_obj, target_count, None


    async def increment_task_generated_count(self, batch_id: str, key_template: str, increment_by: int = 1) -> Optional[int]:
        return await self.redis_batch_store.increment_field(
            key_template=key_template,
            batch_id=batch_id,
            field="generated_count_in_chunk",
            increment_by=increment_by
        )

    async def set_character_task_final_status(self, batch_id: str, key_template: str, status: str, **kwargs):
        fields_to_update = {"status": status}

        if status == "completed":
            final_count = kwargs.get('final_generated_count')
            target_count = kwargs.get('target_count')
            fields_to_update["generated_count_in_chunk"] = final_count
            if kwargs.get('was_empty'):
                fields_to_update["notes"] = "Batch was empty and processed as completed."
            elif final_count is not None and target_count is not None and final_count < target_count:
                fields_to_update["notes"] = "Completed with some specifications skipped or failed."

        elif status == "failed" and kwargs.get('error_message'):
            fields_to_update["error_message"] = str(kwargs['error_message'])[:1024]

        try:
            await self.redis_batch_store.update_fields(
                key_template=key_template,
                batch_id=batch_id,
                fields=fields_to_update,
                ttl_seconds=DEFAULT_TTL_TASK_STATUS if status in ["completed", "completed_with_warnings", "failed"] else None
            )
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении финального статуса батча '{batch_id}': {e}", exc_info=True)

# Удаляем глобальный экземпляр
# task_queue_cache_manager: Optional['TaskQueueCacheManager'] = None