import logging
import asyncio
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from arq import ArqRedis

from game_server.config.provider import config

# ИЗМЕНЕНО: Импорт класса CharacterBatchProcessor
from game_server.Logic.DomainLogic.worker_generator_templates.worker_character_template.character_batch_processor import CharacterBatchProcessor #

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорт CharacterGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import CharacterGenerationSpec #


async def generate_character_batch_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    """
    ARQ-задача для обработки батча генерации персонажей.
    Данные спецификаций извлекаются из Redis и валидируются как CharacterGenerationSpec DTO.
    """
    log_prefix = f"CHAR_TASK_ID({batch_id}):"
    logger.info(f"{log_prefix} Запуск ARQ-задачи для персонажей.")

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

    # ИЗМЕНЕНО: Инстанциируем CharacterBatchProcessor
    character_batch_processor = CharacterBatchProcessor( #
        repository_manager=repository_manager,
        task_queue_cache_manager=task_queue_cache_manager,
        central_redis_client=central_redis_client,
        reference_data_reader=reference_data_reader,
        arq_redis_pool=arq_redis_pool
    )

    try:
        raw_batch_specs: Optional[List[Dict[str, Any]]] = await task_queue_cache_manager.get_task_batch_specs(
            batch_id=batch_id,
            key_template=config.constants.redis.CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
            log_prefix=log_prefix
        )

        if not raw_batch_specs:
            logger.warning(f"{log_prefix} Не удалось получить спецификации батча '{batch_id}' из Redis или они пусты. Завершение задачи.")
            await task_queue_cache_manager.update_task_status(
                batch_id=batch_id,
                key_template=config.constants.redis.CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message="No batch specs found in Redis."
            )
            return

        validated_char_specs: List[CharacterGenerationSpec] = []
        for spec_dict in raw_batch_specs:
            try:
                validated_char_specs.append(CharacterGenerationSpec(**spec_dict))
            except Exception as e:
                logger.error(f"{log_prefix} Ошибка валидации спецификации персонажа из Redis: {e}. Пропускаем элемент: {spec_dict}", exc_info=True)
                raise

        if not validated_char_specs:
            logger.error(f"{log_prefix} Все спецификации батча '{batch_id}' оказались невалидными. Завершение задачи с ошибкой.")
            await task_queue_cache_manager.update_task_status(
                batch_id=batch_id,
                key_template=config.constants.redis.CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message="All character specs failed Pydantic validation."
            )
            return

        # ИЗМЕНЕНО: Вызываем метод process_batch у инстанса CharacterBatchProcessor
        await character_batch_processor.process_batch( #
            redis_worker_batch_id=batch_id,
            task_key_template=config.constants.redis.CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
            batch_specs=validated_char_specs # Передаем валидированные DTO
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи для персонажей успешно выполнена.")
    except Exception as e:
        logger.critical(f"{log_prefix} ОБНАРУЖЕНА ОШИБКА: {e}", exc_info=True)
        try:
            await task_queue_cache_manager.update_task_status(
                batch_id=batch_id,
                key_template=config.constants.redis.CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                status="failed",
                log_prefix=f"TASK({batch_id}):",
                error_message=str(e)
            )
        except Exception as update_e:
            logger.error(f"{log_prefix} Не удалось обновить статус задачи на 'failed' после ошибки: {update_e}", exc_info=True)
        raise