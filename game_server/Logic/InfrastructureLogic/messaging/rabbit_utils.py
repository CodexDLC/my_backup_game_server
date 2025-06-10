# game_server/Logic/InfrastructureLogic/messaging/rabbit_utils.py

import uuid
import json
import logging
from typing import List, Dict, Any, Callable, Optional, Iterator

# Обновленные импорты для Redis и RabbitMQ
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client


logger = logging.getLogger(__name__)

def split_into_batches(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """Разбивает список на батчи указанного размера."""
    if not data or batch_size <= 0: return
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

# 🔥 ИСПРАВЛЕНИЕ: Добавлен task_key_template в сигнатуру функции 🔥
# 🔥 ИСПРАВЛЕНИЕ: Убраны лишние логи отладки 🔥
async def save_batch_data_to_redis(
    batch_id: str,
    batch_specs: List[Dict[str, Any]],
    redis_task_key_template: str, # <--- 🔥 ДОБАВЛЕНО 🔥
    ttl_seconds: int 
) -> bool:
    """
    Сохраняет данные батча в Redis.
    """
    redis_task_key = redis_task_key_template.format(batch_id=batch_id)
    try:
        specs_json = json.dumps(batch_specs)
        
        await central_redis_client.hmset(redis_task_key, {
            "status": "initiation",
            "specs_json": specs_json,
            "target_count_in_chunk": len(batch_specs),
            "generated_count_in_chunk": 0
        })
        await central_redis_client.expire(redis_task_key, ttl_seconds)
        
        # logger.debug(f"Батч '{batch_id}' сохранен в Redis: {redis_task_key} с TTL {ttl_seconds}s.") # УДАЛЕНО/ЗАКОММЕНТИРОВАНО
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении батча '{batch_id}' в Redis: {e}", exc_info=True)
        return False


class TaskDispatcher:
    # ... (методы остались без изменений) ...

    # 🔥 ИСПРАВЛЕНИЕ: Убраны лишние логи отладки из process_and_dispatch_tasks 🔥
    async def process_and_dispatch_tasks(
        self,
        task_list: List[Dict[str, Any]],
        batch_size: int,
        redis_task_key_template: str,
        redis_ttl_seconds: int,
        celery_queue_name: str,
        celery_task_callable: Callable[[str], Any],
        task_type_name: str
    ) -> List[str]:
        """
        Разбивает список задач на батчи, сохраняет в Redis и отправляет в Celery.
        Используется для обработки сырых списков задач.
        """
        if not task_list:
            logger.info(f"Нет задач для {task_type_name}. Пропуск диспетчеризации.")
            return []

        logger.info(f"Начало диспетчеризации {len(task_list)} задач для {task_type_name}...")
        
        worker_batch_chunks = list(split_into_batches(task_list, batch_size))
        logger.info(f"Задачи {task_type_name} разделены на {len(worker_batch_chunks)} рабочих батчей размером до {batch_size}.")

        created_batch_ids: List[str] = []
        for i, chunk_of_specs in enumerate(worker_batch_chunks):
            if not chunk_of_specs:
                continue
            
            redis_worker_batch_id = str(uuid.uuid4())
            
            success = await save_batch_data_to_redis(
                batch_id=redis_worker_batch_id,
                batch_specs=chunk_of_specs,
                redis_task_key_template=redis_task_key_template, # Передаем task_key_template
                ttl_seconds=redis_ttl_seconds
            )
            
            if success:
                try:
                    celery_task_callable.apply_async(
                        args=[redis_worker_batch_id], 
                        queue=celery_queue_name
                    )
                    created_batch_ids.append(redis_worker_batch_id)
                    logger.info(f"Задача для батча {i+1}/{len(worker_batch_chunks)} ({task_type_name}) ID '{redis_worker_batch_id}' успешно поставлена в очередь '{celery_queue_name}'.")
                except Exception as e:
                    logger.error(f"Не удалось поставить задачу для батча ID '{redis_worker_batch_id}' ({task_type_name}) в очередь Celery: {e}", exc_info=True)
            else:
                logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' ({task_type_name}) в Redis. Celery-задача не будет отправлена.")
        
        logger.info(f"Завершена диспетчеризация задач для {task_type_name}. Всего поставлено в очередь: {len(created_batch_ids)} батчей.")
        return created_batch_ids

    # ... (dispatch_existing_batch_id, send_raw_message остаются без изменений) ...