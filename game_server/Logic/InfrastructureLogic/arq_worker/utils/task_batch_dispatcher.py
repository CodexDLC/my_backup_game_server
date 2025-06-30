# game_server/Logic/InfrastructureLogic/arq_worker/utils/task_batch_dispatcher.py

import uuid
import logging
from typing import List, Dict, Any, Optional, Iterator
from arq.connections import ArqRedis

# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.config.provider import config # Для получения TTL по умолчанию

logger = logging.getLogger(__name__)

# --- Вспомогательная утилита ---

def split_into_batches(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """Разбивает список на батчи указанного размера."""
    if not data or batch_size <= 0:
        return iter([])
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


class ArqTaskDispatcher:
    """
    Класс-помощник для централизованной диспетчеризации задач в ARQ.
    Использует RedisBatchStore для сохранения данных батчей.
    """
    # <<< ИЗМЕНЕНО: Конструктор теперь принимает ArqRedis и RedisBatchStore
    def __init__(self, arq_redis_pool: ArqRedis, redis_batch_store: RedisBatchStore):
        self.arq_redis_pool = arq_redis_pool
        self.redis_batch_store = redis_batch_store
        logger.info("✅ ArqTaskDispatcher (v2, RedisBatchStore) инициализирован.")

    async def process_and_dispatch_tasks(
        self,
        task_list: List[Dict[str, Any]],
        batch_size: int,
        key_template: str, # <<< ДОБАВЛЕНО: Шаблон ключа теперь обязателен
        task_arq_name: str,
        task_type_name: str,
    ) -> List[str]:
        """
        Разбивает список задач на батчи, сохраняет в Redis и отправляет в ARQ.
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
            
            # <<< ИЗМЕНЕНО: Используем self.redis_batch_store.save_batch
            batch_data_to_save = {
                "specs": chunk_of_specs,
                "target_count": len(chunk_of_specs),
                "status": "pending"
            }
            
            success = await self.redis_batch_store.save_batch(
                batch_id=redis_worker_batch_id,
                key_template=key_template,
                batch_data=batch_data_to_save,
                ttl_seconds=config.settings.redis.BATCH_TASK_TTL_SECONDS
            )
            
            if success:
                try:
                    await self.arq_redis_pool.enqueue_job(task_arq_name, batch_id=redis_worker_batch_id)
                    created_batch_ids.append(redis_worker_batch_id)
                    logger.info(f"Задача для батча {i+1}/{len(worker_batch_chunks)} ({task_type_name}) ID '{redis_worker_batch_id}' успешно поставлена в очередь ARQ ('{task_arq_name}').")
                except Exception as e:
                    logger.error(f"Не удалось поставить задачу для батча ID '{redis_worker_batch_id}' ({task_type_name}) в очередь ARQ: {e}", exc_info=True)
            else:
                logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' ({task_type_name}) в Redis. ARQ-задача не будет отправлена.")
        
        logger.info(f"Завершена диспетчеризация задач для {task_type_name}. Всего поставлено в очередь: {len(created_batch_ids)} батчей.")
        return created_batch_ids

    async def dispatch_existing_batch_id(
        self,
        batch_id: str,
        task_arq_name: str,
        task_type_name: str,
        *task_args: Any
    ) -> bool:
        """
        Отправляет уже существующий batch_id (который находится в Redis) в ARQ.
        """
        logger.info(f"Начинаем диспетчеризацию существующего батча '{batch_id}' ({task_type_name}) в очередь ARQ ('{task_arq_name}').")
        try:
            # Передаем batch_id как именованный аргумент, как ожидают наши задачи
            await self.arq_redis_pool.enqueue_job(task_arq_name, batch_id=batch_id, *task_args)
            logger.info(f"✅ Существующий батч '{batch_id}' ({task_type_name}) успешно поставлен в очередь ARQ ('{task_arq_name}').")
            return True
        except Exception as e:
            logger.error(f"❌ Не удалось поставить существующий батч '{batch_id}' ({task_type_name}) в очередь ARQ: {e}", exc_info=True)
            return False
