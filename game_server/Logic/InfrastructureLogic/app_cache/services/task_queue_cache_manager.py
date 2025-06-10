# game_server/Logic/InfrastructureLogic/app_cache/services/task_queue_cache_manager.py

import logging
import json
from typing import Any, Dict, List, Optional, Tuple

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    KEY_PREFIX_TASK_QUEUE,
    KEY_PREFIX_TASK_STATUS,
    DEFAULT_TTL_TASK_QUEUE_ITEM,
    DEFAULT_TTL_TASK_STATUS
)

logger = logging.getLogger(__name__)

class TaskQueueCacheManager:
    """
    Высокоуровневый менеджер для кэширования и управления задачами и их статусами в Redis.
    """
    def __init__(self):
        self.redis = central_redis_client
        logger.info("✅ TaskQueueCacheManager инициализирован.")

    # ... все методы, связанные с очередями и статусами, остаются здесь ...
    # (add_task_to_queue, get_task_batch_specs, update_task_status, и т.д.)

    async def get_task_batch_specs(self, batch_id: str, key_template: str, log_prefix: str) -> Optional[List[Dict[str, Any]]]:
        redis_task_key = key_template.format(batch_id=batch_id)
        try:
            task_data_dict = await self.redis.hgetall(redis_task_key)
            if not task_data_dict:
                logger.error(f"{log_prefix} Задачи с ID {batch_id} (ключ: {redis_task_key}) не найдена в Redis.")
                await self.update_task_status(
                    batch_id=batch_id, key_template=key_template, status="failed", 
                    log_prefix=log_prefix, error_message="Batch specs not found"
                )
                return None

            specs_json_str = task_data_dict.get('specs_json')
            if not specs_json_str:
                logger.error(f"{log_prefix} Отсутствует 'specs_json' в задаче {batch_id}.")
                await self.update_task_status(
                    batch_id=batch_id, key_template=key_template, status="failed",
                    log_prefix=log_prefix, error_message="Missing specs_json"
                )
                return None

            batch_specs = json.loads(specs_json_str)
            logger.info(f"{log_prefix} Получено {len(batch_specs)} спецификаций.")
            await self.update_task_status(
                batch_id=batch_id, key_template=key_template, 
                status="in_progress", log_prefix=log_prefix
            )
            return batch_specs
        except Exception as e:
            logger.error(f"{log_prefix} Ошибка при получении спецификаций: {e}", exc_info=True)
            await self.update_task_status(
                batch_id=batch_id, key_template=key_template, status="failed",
                log_prefix=log_prefix, error_message=str(e)
            )
            return None

    async def update_task_status(self, batch_id: str, key_template: str, status: str, log_prefix: str, error_message: Optional[str] = None, ttl_seconds: Optional[int] = None):
        redis_task_key = key_template.format(batch_id=batch_id)
        try:
            async with self.redis.pipeline() as pipe:
                pipe.hset(redis_task_key, "status", status)
                if error_message:
                    pipe.hset(redis_task_key, "error_message", error_message)
                
                if status in ["completed", "completed_with_warnings"] and ttl_seconds is not None:
                    pipe.expire(redis_task_key, ttl_seconds)
                
                await pipe.execute()
            logger.info(f"{log_prefix} Статус задачи '{batch_id}' обновлен на '{status}'.")
        except Exception as e:
            logger.error(f"{log_prefix} Ошибка при обновлении статуса задачи на '{status}': {e}", exc_info=True)
            
    async def get_character_task_specs(self, batch_id: str, key_template: str) -> Tuple[Optional[List], int, Optional[str]]:
        redis_task_key = key_template.format(batch_id=batch_id)
        try:
            task_data_dict = await self.redis.hgetall(redis_task_key)
            if not task_data_dict:
                return None, 0, f"Задача с ключом {redis_task_key} не найдена."

            specs_json = task_data_dict.get('specs_json')
            target_count = int(task_data_dict.get('target_count_in_chunk', '0'))

            if not specs_json:
                error_msg = f"Отсутствует 'specs_json' в задаче {redis_task_key}."
                await self.set_character_task_final_status(
                    batch_id=batch_id, key_template=key_template, 
                    status="failed", error_message=error_msg
                )
                return None, target_count, error_msg

            return json.loads(specs_json), target_count, None
        except Exception as e:
            error_msg = f"Ошибка при извлечении данных задачи {redis_task_key}: {e}"
            logger.error(error_msg, exc_info=True)
            try:
                await self.set_character_task_final_status(
                    batch_id=batch_id, key_template=key_template, 
                    status="failed", error_message=str(e)
                )
            except Exception as update_e:
                logger.error(f"Не удалось обновить статус до 'failed' для {redis_task_key}: {update_e}")
            return None, 0, error_msg

    async def increment_task_generated_count(self, batch_id: str, key_template: str, increment_by: int = 1) -> Optional[int]:
        redis_task_key = key_template.format(batch_id=batch_id)
        try:
            return await self.redis.hincrby(redis_task_key, "generated_count_in_chunk", increment_by)
        except Exception as e:
            logger.error(f"Ошибка hincrby для {redis_task_key}: {e}", exc_info=True)
            return None

    async def set_character_task_final_status(self, batch_id: str, key_template: str, status: str, **kwargs):
        redis_task_key = key_template.format(batch_id=batch_id)
        payload = {"status": status}
        
        if status == "completed":
            final_count = kwargs.get('final_generated_count')
            target_count = kwargs.get('target_count')
            payload["generated_count_in_chunk"] = final_count 
            if kwargs.get('was_empty'):
                payload["notes"] = "Batch was empty and processed as completed."
            elif final_count is not None and target_count is not None and final_count < target_count:
                payload["notes"] = "Completed with some specifications skipped or failed."
        
        elif status == "failed" and kwargs.get('error_message'):
            payload["error_message"] = str(kwargs['error_message'])[:1024]
            
        try:
            await self.redis.hmset(redis_task_key, payload) 
        except Exception as e:
            logger.error(f"Ошибка hmset для {redis_task_key}: {e}", exc_info=True)
            
    # 🔥 ИЗМЕНЕНИЕ: Метод get_weighted_random_id УДАЛЕН отсюда. Его место в ReferenceDataReader.

# Создаем единственный экземпляр менеджера
task_queue_cache_manager = TaskQueueCacheManager()
