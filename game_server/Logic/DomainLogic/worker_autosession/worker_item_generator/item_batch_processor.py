# game_server/Logic/DomainLogic/handlers_template/worker_item_generator/item_batch_processor.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
# 🔥 ИЗМЕНЕНИЕ: УДАЛЕН импорт CentralRedisClient, так как он больше не нужен здесь 🔥
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.services.logging.logging_setup import logger

from .handler_utils.item_db_persistence import persist_item_templates_to_db
# Импортируем функции, которые теперь не принимают redis_client
from .handler_utils.item_redis_operations import get_batch_specs_from_redis, update_redis_task_status
# Исправлено: теперь item_template_creation_utils принимает redis_client
from .handler_utils.item_template_creation_utils import generate_item_templates_from_specs 

REDIS_TASK_COMPLETION_TTL_SECONDS: int = 3600 # 1 час


class ItemBatchProcessor:
    """
    Оркестратор для обработки батчей задач.
    Теперь не принимает и не использует экземпляр Redis-клиента напрямую,
    так как менеджеры Redis используют глобальный клиент.
    """
    # 🔥 ИЗМЕНЕНИЕ: Удален redis_client из конструктора 🔥
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # 🔥 ИЗМЕНЕНИЕ: Удалена ссылка на redis_client 🔥
        # self.redis_client = redis_client
        logger.info("ItemBatchProcessor инициализирован.")

    async def process_batch(self, redis_worker_batch_id: str, task_key_template: str) -> None:
        """Основной метод для обработки одного батча задач."""
        log_prefix = f"ITEM_BATCH_PROCESSOR_ID({redis_worker_batch_id}):"
        logger.info(f"{log_prefix} Начало обработки батча шаблонов предметов.")

        # Вызов get_batch_specs_from_redis не требует redis_client, т.к. TaskQueueCacheManager самодостаточен
        batch_specs = await get_batch_specs_from_redis(
            redis_worker_batch_id=redis_worker_batch_id,
            task_key_template=task_key_template,
            log_prefix=log_prefix,
        )

        if batch_specs is None:
            logger.warning(f"{log_prefix} Batch specs не найдены или произошла ошибка. Завершение обработки.")
            return

        try:
            # 🔥 ИЗМЕНЕНИЕ: generate_item_templates_from_specs теперь не принимает redis_client 🔥
            generated_templates = await generate_item_templates_from_specs(
                batch_specs=batch_specs,
                log_prefix=log_prefix,
            )

            if not generated_templates:
                logger.warning(f"{log_prefix} Ни одного шаблона не сгенерировано. Обновляем статус.")
                # Вызов update_redis_task_status не требует redis_client
                await update_redis_task_status(
                    redis_worker_batch_id=redis_worker_batch_id,
                    task_key_template=task_key_template,
                    status="completed_with_warnings",
                    log_prefix=log_prefix,
                    error_message="No templates generated from specs",
                    ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                )
                return

            success = await persist_item_templates_to_db(
                db_session=self.db_session,
                generated_templates=generated_templates,
                log_prefix=log_prefix
            )

            status_to_set = "completed" if success else "failed"
            error_msg = None if success else "Failed to persist templates to DB"
            
            # Вызов update_redis_task_status не требует redis_client
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status=status_to_set,
                log_prefix=log_prefix,
                error_message=error_msg,
                ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
            )
            if not success:
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"{log_prefix} Критическая ошибка при обработке батча предметов: {e}", exc_info=True)
            # Вызов update_redis_task_status не требует redis_client
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status="failed",
                log_prefix=log_prefix,
                error_message=str(e),
            )
            raise
