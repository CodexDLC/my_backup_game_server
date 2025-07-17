# game_server/Logic/DomainLogic/worker_generator_templates/worker_item_template/item_batch_processor.py

import logging
from typing import List, Dict, Any, Callable # Добавлен Callable
from sqlalchemy.ext.asyncio import AsyncSession # Добавлен AsyncSession

# Импортируем RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
# Импортируем интерфейс ФАБРИКИ конкретного репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
from game_server.contracts.dtos.orchestrator.data_models import ItemGenerationSpec


from .handler_utils.item_redis_operations import update_redis_task_status
from .handler_utils.item_template_creation_utils import generate_item_templates_from_specs
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader

REDIS_TASK_COMPLETION_TTL_SECONDS: int = 3600 # 1 час


class ItemBatchProcessor:
    """
    Оркестратор для обработки батчей задач по созданию предметов.
    Теперь принимает фабрику репозитория и работает с сессией, переданной извне.
    """
    def __init__(
        self,
        # 🔥 ИЗМЕНЕНО: Теперь принимаем ФАБРИКУ IEquipmentTemplateRepository
        equipment_template_repo_factory: Callable[[AsyncSession], IEquipmentTemplateRepository],
        redis_batch_store: RedisBatchStore,
        reference_data_reader: ReferenceDataReader,
        logger: logging.Logger,
    ):
        # 🔥 ИЗМЕНЕНО: Сохраняем фабрику equipment_template_repo
        self._equipment_template_repo_factory = equipment_template_repo_factory
        self.logger = logger
        self.redis_batch_store = redis_batch_store
        self.reference_data_reader = reference_data_reader
        self.logger.info("ItemBatchProcessor инициализирован.")

    async def process_batch(
        self,
        session: AsyncSession, # <--- ДОБАВЛЕНО: Теперь метод принимает активную сессию
        redis_worker_batch_id: str,
        task_key_template: str,
        batch_specs: List[ItemGenerationSpec]
    ) -> None:
        """
        Основной метод для обработки одного батча задач.
        Выполняется в рамках переданной сессии.
        """
        log_prefix = f"ITEM_BATCH_PROCESSOR_ID({redis_worker_batch_id}):"
        self.logger.info(f"{log_prefix} Начало обработки батча шаблонов предметов в рамках внешней транзакции.")

        # Создаем экземпляр репозитория с активной сессией, переданной извне
        equipment_template_repo = self._equipment_template_repo_factory(session)

        if not batch_specs:
            self.logger.warning(f"{log_prefix} Получен пустой список спецификаций. Завершение.")
            await update_redis_task_status(
                redis_worker_batch_id=redis_worker_batch_id,
                task_key_template=task_key_template,
                status="completed_with_warnings",
                log_prefix=log_prefix,
                error_message="Received empty batch specs list",
                ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                redis_batch_store=self.redis_batch_store,
                final_generated_count=0
            )
            # Откат транзакции будет выполнен вышестоящим ARQ-таском, если произойдет исключение
            return

        try:
            generated_templates = await generate_item_templates_from_specs(
                batch_specs=batch_specs,
                log_prefix=log_prefix,
                reference_data_reader=self.reference_data_reader,
            )

            if not generated_templates:
                self.logger.warning(f"{log_prefix} Ни одного шаблона не сгенерировано.")
                await update_redis_task_status(
                    redis_worker_batch_id=redis_worker_batch_id,
                    task_key_template=task_key_template,
                    status="completed_with_warnings",
                    log_prefix=log_prefix,
                    error_message="No templates generated from specs",
                    ttl_seconds_on_completion=REDIS_TASK_COMPLETION_TTL_SECONDS,
                    redis_batch_store=self.redis_batch_store,
                    final_generated_count=0
                )
                # Откат транзакции будет выполнен вышестоящим ARQ-таском, если произойдет исключение
                return

            self.logger.info(f"{log_prefix} Успешно сгенерировано {len(generated_templates)} шаблонов предметов.")

            try:
                # 🔥 ИСПОЛЬЗУЕМ СОЗДАННЫЙ ЭКЗЕМПЛЯР РЕПОЗИТОРИЯ
                success_count = await equipment_template_repo.upsert_many(
                    generated_templates
                )
                success = success_count > 0
                if not success:
                    self.logger.warning(f"{log_prefix} Массовое сохранение не выполнено, 0 записей обработано.")
            except Exception as e:
                self.logger.error(f"{log_prefix} Ошибка при массовом сохранении шаблонов в БД: {e}", exc_info=True)
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
                redis_batch_store=self.redis_batch_store,
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
                redis_batch_store=self.redis_batch_store,
                final_generated_count=0
            )
            # Откат транзакции будет выполнен вышестоящим ARQ-таском
            raise