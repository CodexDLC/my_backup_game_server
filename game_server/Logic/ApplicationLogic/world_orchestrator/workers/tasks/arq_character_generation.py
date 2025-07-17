# game_server\Logic\ApplicationLogic\world_orchestrator\workers\tasks\arq_character_generation.py

import logging
from typing import Dict, Any, Optional, List, Callable
# import inject # 🔥 УДАЛЕНО: inject больше не нужен для autoparams здесь
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем наш transactional декоратор
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импорты классов/интерфейсов, которые будут получены из ctx
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.character_batch_processor import CharacterBatchProcessor
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader


from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.config.constants.arq import KEY_CHARACTER_GENERATION_TASK
from game_server.contracts.dtos.orchestrator.data_models import CharacterGenerationSpec


# 🔥 УДАЛЕНО: @inject.autoparams() полностью
@transactional(AsyncSessionLocal)
async def generate_character_batch_task(
    session: AsyncSession, # <--- Сессия от @transactional
    ctx: Dict[str, Any],    # <--- Контекст ARQ (теперь используем его для зависимостей)
    batch_id: str,          # <--- batch_id от ARQ
    **kwargs,               # Для любых дополнительных аргументов ARQ
) -> None:
    """
    ARQ-задача для обработки батча генерации персонажей.
    Вся операция обернута в единую транзакцию.
    """
    # 🔥 ИЗМЕНЕНИЕ: Получаем зависимости из ctx
    logger: logging.Logger = ctx["logger"]
    redis_batch_store: RedisBatchStore = ctx["redis_batch_store"]
    reference_data_reader: IReferenceDataReader = ctx["redis_reader"] # Имя "redis_reader" в ctx
    character_pool_repo_factory: Callable[[AsyncSession], ICharacterPoolRepository] = ctx["character_pool_repo_factory"]


    log_prefix = f"CHAR_TASK_ID({batch_id}):"
    logger.info(f"{log_prefix} Запуск ARQ-задачи для персонажей (транзакционно).")

    try:
        # Создаем обработчик батча, передавая ему фабрику репозитория
        character_batch_processor = CharacterBatchProcessor(
            char_pool_repo_factory=character_pool_repo_factory,
            redis_batch_store=redis_batch_store,
            reference_data_reader=reference_data_reader,
            logger=logger
        )

        # Получаем данные батча через redis_batch_store.load_batch
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
                logger.error(f"{log_prefix} Ошибка валидации спецификации: {e}. Пропускаем: {spec_dict}", exc_info=True)
                raise

        if not validated_char_specs:
            logger.error(f"{log_prefix} Все спецификации батча '{batch_id}' оказались невалидными.")
            return

        # --- Вызов основной логики ---
        # Передаем активную сессию в CharacterBatchProcessor
        await character_batch_processor.process_batch(
            session=session,
            redis_worker_batch_id=batch_id,
            task_key_template=KEY_CHARACTER_GENERATION_TASK,
            batch_specs=validated_char_specs
        )
        logger.info(f"{log_prefix} Асинхронная логика задачи для персонажей успешно выполнена.")

    except Exception as e:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА в ARQ-задаче: {e}", exc_info=True)
        raise