# game_server/Logic/InfrastructureLogic/celery/task/tasks_item_generation.py

import asyncio
from game_server.Logic.InfrastructureLogic.celery.celery_app import app 

from game_server.Logic.DomainLogic.worker_autosession.worker_item_generator.item_batch_processor import ItemBatchProcessor
from game_server.services.logging.logging_setup import logger 

from game_server.Logic.InfrastructureLogic.DataAccessLogic.worker_db_utils import get_worker_db_session

# 🔥 ИЗМЕНЕНИЕ: Теперь импортируем глобальный экземпляр CentralRedisClient 🔥
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client 
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE 


@app.task(
    bind=True,
    name="item_generation.process_item_generation_batch_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionRefusedError, TimeoutError,), # Сохраняем эти, плюс те, что были изначально
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=True
)
def process_item_generation_batch_task(self, redis_worker_batch_id: str):
    """
    Точка входа в Celery-задачу.
    Запускает асинхронную логику с помощью asyncio.run().
    """
    log_prefix = f"ITEM_TASK_ID({redis_worker_batch_id}):"
    try:
        logger.info(f"{log_prefix} Запуск Celery-задачи для предметов.")
        asyncio.run(
            _run_async_item_task_logic(self, redis_worker_batch_id)
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи для предметов успешно выполнена.")
    except Exception as e:
        error_type = type(e).__name__
        error_message_full = f"{log_prefix} 🔥 ОТЛАДКА: Обнаружена ошибка ({error_type}) при обработке предметов: {e}"
        logger.critical(error_message_full, exc_info=True)
        raise self.retry(exc=e, countdown=self.default_retry_delay)


async def _run_async_item_task_logic(self, redis_worker_batch_id: str):
    """
    Асинхронная логика задачи.
    Теперь переинициализирует глобальный Redis-клиент для текущего Event Loop.
    """
    inner_log_prefix = f"ITEM_TASK_ASYNC_LOGIC_ID({redis_worker_batch_id}):"
    
    try:
        # 🔥 ИЗМЕНЕНИЕ: Переинициализируем соединение Redis для текущего Event Loop 🔥
        await central_redis_client.reinitialize_connection()

        async with get_worker_db_session() as db_session:
            item_batch_processor = ItemBatchProcessor(db_session=db_session)
            
            await item_batch_processor.process_batch(
                redis_worker_batch_id,
                ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE 
            )

    except Exception as e:
        logger.error(f"{inner_log_prefix} Ошибка во внутренней асинхронной логике предметов: {e}", exc_info=True)
        raise e
    finally:
        # В данном сценарии (использование asyncio.run с глобальным клиентом)
        # aioredis сам управляет пулом соединений. Явное закрытие здесь не требуется
        # и может привести к проблемам с переиспользованием.
        pass 
