# game_server/Logic/InfrastructureLogic/generator_utils/generator_redis_utils.py

from typing import List, Dict, Any
from game_server.services.logging.logging_setup import logger

# --- НОВЫЕ ИМПОРТЫ ---
from game_server.Logic.InfrastructureLogic.app_cache.services import task_queue_cache_manager

async def save_batch_data_to_redis(
    batch_id: str,
    batch_specs: List[Dict[str, Any]],
    task_key_template: str
) -> bool:
    """
    Сохраняет батч данных в Redis, используя TaskQueueCacheManager.
    Больше не принимает redis_client.
    """
    try:
        # БЫЛО: Прямая работа с Redis
        # СТАЛО: Вызов метода менеджера, который инкапсулирует всю логику
        await task_queue_cache_manager.save_task_batch(
            batch_id=batch_id,
            batch_specs=batch_specs,
            task_key_template=task_key_template
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении батча {batch_id} в Redis через менеджер: {e}", exc_info=True)
        return False