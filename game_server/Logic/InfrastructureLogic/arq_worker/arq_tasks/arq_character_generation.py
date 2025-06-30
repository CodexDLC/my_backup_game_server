# game_server/Logic/InfrastructureLogic/arq_worker/arq_tasks/arq_character_generation.py
import logging
from typing import Dict, Any, Optional, List

from game_server.common_contracts.dtos.orchestrator_dtos import CharacterGenerationSpec
from game_server.Logic.DomainLogic.worker_generator_templates.worker_character_template.character_batch_processor import CharacterBatchProcessor
from game_server.config.logging.logging_setup import app_logger as logger

# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore и константу ключа
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.config.constants.redis_key.task_keys import KEY_CHARACTER_GENERATION_TASK

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager


async def generate_character_batch_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    """
    ARQ-задача для обработки батча генерации персонажей.
    """
    log_prefix = f"CHAR_TASK_ID({batch_id}):"
    logger.info(f"{log_prefix} Запуск ARQ-задачи для персонажей.")

    try:
        # --- Получение зависимостей из контекста ARQ ---
        # <<< ИЗМЕНЕНО: Извлекаем зависимости напрямую из ctx
        redis_batch_store: RedisBatchStore = ctx.get('redis_batch_store')
        reference_data_reader: IReferenceDataReader = ctx.get('reference_data_reader')
        repository_manager: RepositoryManager = ctx.get('repository_manager')

        if not all([redis_batch_store, reference_data_reader, repository_manager]):
            raise RuntimeError("Один или несколько необходимых менеджеров не были найдены в контексте ARQ.")

        # <<< ИЗМЕНЕНО: Создаем обработчик батча с правильным набором зависимостей
        character_batch_processor = CharacterBatchProcessor(
            repository_manager=repository_manager,
            redis_batch_store=redis_batch_store,
            reference_data_reader=reference_data_reader
        )

        # <<< ИЗМЕНЕНО: Получаем данные батча через redis_batch_store.load_batch
        batch_data = await redis_batch_store.load_batch(
            batch_id=batch_id,
            key_template=KEY_CHARACTER_GENERATION_TASK
        )

        if not batch_data or 'specs' not in batch_data:
            logger.warning(f"{log_prefix} Не удалось получить данные батча '{batch_id}' или они не содержат 'specs'.")
            return

        raw_batch_specs = batch_data['specs']

        # --- Валидация данных ---
        validated_char_specs: List[CharacterGenerationSpec] = []
        for spec_dict in raw_batch_specs:
            try:
                validated_char_specs.append(CharacterGenerationSpec(**spec_dict))
            except Exception as e:
                logger.error(f"{log_prefix} Ошибка валидации спецификации персонажа: {e}. Пропускаем: {spec_dict}", exc_info=True)
                raise

        if not validated_char_specs:
            logger.error(f"{log_prefix} Все спецификации батча '{batch_id}' оказались невалидными.")
            return

        # --- Вызов основной логики ---
        await character_batch_processor.process_batch(
            redis_worker_batch_id=batch_id,
            task_key_template=KEY_CHARACTER_GENERATION_TASK, # Передаем правильный шаблон ключа
            batch_specs=validated_char_specs
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи для персонажей успешно выполнена.")
    
    except Exception as e:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА в ARQ-задаче: {e}", exc_info=True)
        raise
