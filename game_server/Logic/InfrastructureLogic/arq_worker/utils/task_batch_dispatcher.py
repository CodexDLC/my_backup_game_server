# game_server\Logic\InfrastructureLogic\arq_worker\utils\task_batch_dispatcher.py

import uuid # Все еще нужен для генерации batch_id
# import json # УДАЛЕНО: Больше не нужен, если все сериализуется в TaskQueueCacheManager
import logging
from typing import List, Dict, Any, Callable, Optional, Iterator
from arq.connections import ArqRedis # Импортируем для типизации arq_redis_pool

# Импортируем наш обновленный CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.constants.redis import KEY_PREFIX_TASK_QUEUE # Все еще нужен для формирования ключа

# ИМПОРТИРУЕМ TaskQueueCacheManager из новой доменной папки
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager # ИЗМЕНЕНО
# ДОБАВЛЕНО: Импорт интерфейса TaskQueueCacheManager для типизации
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager


logger = logging.getLogger(__name__)

# --- Вспомогательные утилиты ---

def split_into_batches(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """Разбивает список на батчи указанного размера."""
    if not data or batch_size <= 0:
        return iter([]) # Возвращаем пустой итератор для корректности
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


class ArqTaskDispatcher: # Класс переименован в ArqTaskDispatcher
    """
    Класс-помощник для централизованной диспетчеризации задач в ARQ.
    Использует TaskQueueCacheManager для сохранения данных батчей.
    """
    # Конструктор теперь принимает подключенный ArqRedis пул и CentralRedisClient
    def __init__(self, arq_redis_pool: ArqRedis, redis_client: CentralRedisClient):
        self.arq_redis_pool = arq_redis_pool
        self.redis_client = redis_client # Будем использовать для передачи в TaskQueueCacheManager
        # Инициализируем TaskQueueCacheManager здесь
        # ИЗМЕНЕНО: Инициализируем с использованием интерфейса (если TaskQueueCacheManager реализует ITaskQueueCacheManager)
        self.task_queue_manager: ITaskQueueCacheManager = TaskQueueCacheManager(redis_client=redis_client)
        logger.info("✅ ArqTaskDispatcher инициализирован.")

    async def process_and_dispatch_tasks(
        self,
        task_list: List[Dict[str, Any]],
        batch_size: int,
        # redis_ttl_seconds: int, # УДАЛЕНО: Этот аргумент больше не нужен
        task_arq_name: str, # Принимаем строковое имя ARQ-задачи
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
            
            # 🔥 ИСПРАВЛЕНИЕ: Используем TaskQueueCacheManager.add_task_to_queue для сохранения
            success = await self.task_queue_manager.add_task_to_queue(
                batch_id=redis_worker_batch_id,
                key_template=KEY_PREFIX_TASK_QUEUE, # Используем KEY_PREFIX_TASK_QUEUE
                specs=chunk_of_specs,
                target_count=len(chunk_of_specs),
                initial_status="pending",
                # ttl_seconds=redis_ttl_seconds # <--- ttl_seconds управляется внутри add_task_to_queue с DEFAULT_TTL_TASK_STATUS
            )
            
            if success:
                try:
                    await self.arq_redis_pool.enqueue_job(task_arq_name, redis_worker_batch_id)

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
        task_arq_name: str, # Принимаем строковое имя ARQ-задачи
        task_type_name: str,
        *task_args: Any
    ) -> bool:
        """
        Отправляет уже существующий batch_id (который находится в Redis) в ARQ.
        """
        logger.info(f"Начинаем диспетчеризацию существующего батча '{batch_id}' ({task_type_name}) в очередь ARQ ('{task_arq_name}').")
        try:
            await self.arq_redis_pool.enqueue_job(task_arq_name, batch_id, *task_args)
            logger.info(f"✅ Существующий батч '{batch_id}' ({task_type_name}) успешно поставлен в очередь ARQ ('{task_arq_name}').")
            return True
        except Exception as e:
            logger.error(f"❌ Не удалось поставить существующий батч '{batch_id}' ({task_type_name}) в очередь ARQ: {e}", exc_info=True)
            return False

# Глобальный экземпляр ArqTaskDispatcher будет инициализирован в FastAPI lifespan или ARQ worker startup.
# Он не создается здесь напрямую.