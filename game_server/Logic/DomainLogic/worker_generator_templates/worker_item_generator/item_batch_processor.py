import logging
from typing import List, Dict, Any, Optional
# from sqlalchemy.ext.asyncio import AsyncSession # Эту строку можно удалить, если AsyncSession больше нигде не используется напрямую в этом файле

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Изменено: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager #
# УДАЛЕНО: from .handler_utils.item_db_persistence import persist_item_templates_to_db
# УДАЛЕНО: from .handler_utils.item_redis_operations import get_batch_specs_from_redis # Мы больше не будем получать specs здесь
from .handler_utils.item_redis_operations import update_redis_task_status # update_redis_task_status остается
from .handler_utils.item_template_creation_utils import generate_item_templates_from_specs

from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader

# ДОБАВЛЕНО: Импорт ItemGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import ItemGenerationSpec #


REDIS_TASK_COMPLETION_TTL_SECONDS: int = 3600 # 1 час


class ItemBatchProcessor:
    """
    Оркестратор для обработки батчей задач.
    Теперь принимает все необходимые менеджеры через конструктор, включая RepositoryManager.
    Метод process_batch теперь принимает уже валидированные ItemGenerationSpec DTO.
    """
    def __init__(
        self,
        repository_manager: RepositoryManager,
        task_queue_cache_manager: TaskQueueCacheManager,
        central_redis_client: CentralRedisClient,
        reference_data_reader: ReferenceDataReader
    ):
        self.repository_manager = repository_manager
        self.logger = logger
        self.task_queue_cache_manager = task_queue_cache_manager
        self.central_redis_client = central_redis_client
        self.reference_data_reader = reference_data_reader

        logger.info("ItemBatchProcessor инициализирован.")

    # ИЗМЕНЕНО: process_batch теперь принимает batch_specs как List[ItemGenerationSpec]
    async def process_batch(
        self,
        redis_worker_batch_id: str,
        task_key_template: str,
        batch_specs: List[ItemGenerationSpec] # <--- ИЗМЕНЕНО: Теперь принимает DTO
    ) -> None:
        """Основной метод для обработки одного батча задач."""
        log_prefix = f"ITEM_BATCH_PROCESSOR_ID({redis_worker_batch_id}):"
        logger.info(f"{log_prefix} Начало обработки батча шаблонов предметов.")



        if not batch_specs: # Проверка, если список пуст
            self.logger.warning(f"{log_prefix} Получен пустой список спецификаций для обработки. Завершение.")
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status="completed_with_warnings",
                log_prefix=log_prefix,
                error_message="Received empty batch specs list",
                ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                task_queue_cache_manager=self.task_queue_cache_manager,
                final_generated_count=0
            )
            return


        try:

            generated_templates = await generate_item_templates_from_specs(
                batch_specs=batch_specs, # <--- Передаем DTO объекты
                log_prefix=log_prefix,
                reference_data_reader=self.reference_data_reader,
            )

            if not generated_templates:
                self.logger.warning(f"{log_prefix} Ни одного шаблона не сгенерировано. Обновляем статус.")
                await update_redis_task_status(
                    redis_worker_batch_id=redis_worker_batch_id,
                    task_key_template=task_key_template,
                    status="completed_with_warnings",
                    log_prefix=log_prefix,
                    error_message="No templates generated from specs",
                    ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                    task_queue_cache_manager=self.task_queue_cache_manager,
                    final_generated_count=0
                )
                return

            self.logger.info(f"{log_prefix} Успешно сгенерировано {len(generated_templates)} шаблонов предметов.")

            try:
                success_count = await self.repository_manager.equipment_templates.upsert_many(
                    generated_templates
                )
                success = success_count > 0
                if not success:
                    self.logger.warning(f"{log_prefix} Массовое сохранение не выполнено успешно, 0 записей обработано.")
            except Exception as e:
                self.logger.error(f"{log_prefix} Ошибка при массовом сохранении шаблонов в БД через RepositoryManager: {e}", exc_info=True)
                success = False
                
            status_to_set = "completed" if success else "failed"
            error_msg = None if success else "Failed to persist templates to DB"
            
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status=status_to_set,
                log_prefix=log_prefix,
                error_message=error_msg,
                ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                task_queue_cache_manager=self.task_queue_cache_manager,
                final_generated_count=len(generated_templates) if success else 0
            )
            if not success:
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"{log_prefix} Критическая ошибка при обработке батча предметов: {e}", exc_info=True)
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status="failed",
                log_prefix=log_prefix,
                error_message=str(e),
                task_queue_cache_manager=self.task_queue_cache_manager,
                final_generated_count=0
            )
            raise