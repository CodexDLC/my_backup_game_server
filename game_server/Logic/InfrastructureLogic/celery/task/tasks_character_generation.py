# game_server/Logic/InfrastructureLogic/celery/task/tasks_character_generation.py

import asyncio
from game_server.Logic.InfrastructureLogic.celery.celery_app import app
from game_server.services.logging.logging_setup import logger

# --- ИЗМЕНЕНИЯ В ИМПОРТАХ ---
# Импортируем глобальный экземпляр CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client

# Импортируем наш "чистый" процессор и утилиту для сессии БД
from game_server.Logic.InfrastructureLogic.DataAccessLogic.worker_db_utils import get_worker_db_session
from game_server.Logic.DomainLogic.worker_autosession.worker_character_template.character_batch_processor import process_character_batch_logic

# Импорты констант
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_generator import (
    CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
    HIGHEST_QUALITY_LEVEL_NAME
)
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_character import (
    TARGET_POOL_QUALITY_DISTRIBUTION
)


@app.task(
    bind=True,
    name="character_generation.process_character_generation_batch_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionRefusedError, TimeoutError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=True
)
def process_character_generation_batch_task(self, redis_worker_batch_id: str):
    """
    Точка входа в Celery-задачу.
    Запускает асинхронную логику с помощью asyncio.run().
    """
    log_prefix = f"TASK_ID({redis_worker_batch_id}):"
    try:
        logger.info(f"{log_prefix} Запуск Celery-задачи для персонажей.")
        asyncio.run(
            _run_async_task_logic(self, redis_worker_batch_id)
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи успешно выполнена.")
    except Exception as e:
        error_type = type(e).__name__
        error_message_full = f"{log_prefix} 🔥 ОТЛАДКА: Обнаружена ошибка ({error_type}). Останавливаю работу для анализа: {e}"
        logger.critical(error_message_full, exc_info=True)
        raise self.retry(exc=e, countdown=self.default_retry_delay)


async def _run_async_task_logic(self, redis_worker_batch_id: str):
    """Асинхронная логика задачи, теперь без управления Redis-клиентом."""
    inner_log_prefix = f"TASK_ASYNC_LOGIC_ID({redis_worker_batch_id}):"
    
    try:
        # 🔥 ИЗМЕНЕНИЕ: Переинициализируем соединение Redis для текущего Event Loop 🔥
        await central_redis_client.reinitialize_connection()

        async with get_worker_db_session() as db_session:
            await process_character_batch_logic(
                redis_worker_batch_id=redis_worker_batch_id,
                db_session=db_session,
                task_key_template=CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                target_quality_distribution=TARGET_POOL_QUALITY_DISTRIBUTION,
                highest_quality_level_name=HIGHEST_QUALITY_LEVEL_NAME
            )
    except Exception as e:
        logger.error(f"{inner_log_prefix} Ошибка во внутренней асинхронной логике: {e}", exc_info=True)
        raise e
    finally:
        # Не обязательно закрывать здесь, так как GlobalRedisClient управляет пулом.
        # Однако, если вы хотите быть абсолютно уверенными, что соединение не будет использоваться
        # в другом Event Loop после завершения этой задачи, можно вызвать close,
        # но это может повлиять на производительность из-за постоянного пересоздания.
        # Оставим это на усмотрение aioredis и его пула соединений.
        pass
