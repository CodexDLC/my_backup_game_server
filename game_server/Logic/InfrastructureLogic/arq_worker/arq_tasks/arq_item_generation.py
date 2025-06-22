import logging
from typing import Dict, Any, Optional, List

from arq import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.DomainLogic.worker_generator_templates.worker_item_generator.item_batch_processor import ItemBatchProcessor
from game_server.config.constants.redis import ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.config.provider import config

# ДОБАВЛЕНО: Импорт ItemGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import ItemGenerationSpec #


async def process_item_generation_batch_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    """
    ARQ-задача для обработки батча генерации предметов.
    Зависимости теперь берутся из ctx и передаются в ItemBatchProcessor.
    Данные спецификаций извлекаются из Redis и валидируются как ItemGenerationSpec DTO.
    """
    log_prefix = f"ITEM_TASK_ID({batch_id}):"
    logger.info(f"{log_prefix} Запуск ARQ-задачи для предметов.")

    db_session: AsyncSession = ctx["db_session"]
    arq_redis_pool: ArqRedis = ctx["redis"]
    app_managers = ctx.get('app_managers')

    if not app_managers:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: 'app_managers' не найден в контексте ARQ воркера. Проверьте arq_worker_settings.py.")
        raise RuntimeError("'app_managers' not initialized in ARQ worker context.")

    task_queue_cache_manager: ITaskQueueCacheManager = app_managers.get('task_queue_cache_manager')
    central_redis_client: CentralRedisClient = app_managers.get('central_redis_client')
    reference_data_reader: IReferenceDataReader = app_managers.get('reference_data_reader')
    repository_manager: RepositoryManager = ctx['repository_manager']

    if (
        task_queue_cache_manager is None or
        central_redis_client is None or
        reference_data_reader is None or
        repository_manager is None
    ):
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Один или несколько менеджеров приложения (из app_managers/ctx) не инициализированы или не переданы в ARQ-контекст!")
        raise RuntimeError("Required app managers are None in ARQ worker context.")

    # Инициализация ItemBatchProcessor
    item_batch_processor = ItemBatchProcessor(
        repository_manager=repository_manager,
        task_queue_cache_manager=task_queue_cache_manager,
        central_redis_client=central_redis_client,
        reference_data_reader=reference_data_reader
    )

    try:
        # ДОБАВЛЕНО: Извлекаем сырые спецификации из Redis
        raw_batch_specs: Optional[List[Dict[str, Any]]] = await task_queue_cache_manager.get_task_batch_specs( #
            batch_id=batch_id,
            key_template=ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
            log_prefix=log_prefix
        )

        if not raw_batch_specs:
            logger.warning(f"{log_prefix} Не удалось получить спецификации батча '{batch_id}' из Redis или они пусты. Завершение задачи.")
            await task_queue_cache_manager.update_task_status( #
                batch_id=batch_id,
                key_template=config.constants.redis.ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message="No batch specs found in Redis."
            )
            return

        # ДОБАВЛЕНО: Валидация и преобразование сырых словарей в Pydantic DTO
        validated_item_specs: List[ItemGenerationSpec] = [] #
        for spec_dict in raw_batch_specs:
            try:
                validated_item_specs.append(ItemGenerationSpec(**spec_dict)) #
            except Exception as e:
                logger.error(f"{log_prefix} Ошибка валидации спецификации предмета из Redis: {e}. Пропускаем элемент: {spec_dict}", exc_info=True)
                # Если валидация одного элемента провалилась, можно решить пропустить его
                # или же пробросить исключение для всей задачи, если любая ошибка критична.
                raise # Если хотим, чтобы любая ошибка валидации прерывала задачу

        if not validated_item_specs:
            logger.error(f"{log_prefix} Все спецификации батча '{batch_id}' оказались невалидными. Завершение задачи с ошибкой.")
            await task_queue_cache_manager.update_task_status( #
                batch_id=batch_id,
                key_template=config.constants.redis.ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message="All item specs failed Pydantic validation."
            )
            return

        # ИЗМЕНЕНО: Передаем валидированные DTO в process_batch
        # Это потребует, чтобы ItemBatchProcessor.process_batch был обновлен
        # для приема List[ItemGenerationSpec] вместо List[Dict[str, Any]]
        await item_batch_processor.process_batch( #
            redis_worker_batch_id=batch_id,
            task_key_template=ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
            batch_specs=validated_item_specs # <--- ДОБАВЛЕНО/ИЗМЕНЕНО: Передаем DTO объекты
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи для предметов успешно выполнена.")
    except Exception as e:
        logger.critical(f"{log_prefix} ОБНАРУЖЕНА КРИТИЧЕСКАЯ ОШИБКА в ARQ-задаче: {e}", exc_info=True)
        try:
            await task_queue_cache_manager.update_task_status( #
                batch_id=batch_id,
                key_template=config.constants.redis.ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message=str(e)
            )
        except Exception as update_e:
            logger.error(f"{log_prefix} Не удалось обновить статус задачи на 'failed' после ошибки: {update_e}", exc_info=True)
        raise