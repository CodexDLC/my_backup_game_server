# game_server/Logic/DomainLogic/worker_generator_templates/worker_character_template/character_batch_processor.py

import logging
from typing import List, Dict, Any, Optional
from collections import Counter

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.DomainLogic.worker_generator_templates.generator_name.name_orchestrator import NameOrchestrator
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.common_contracts.dtos.orchestrator_dtos import CharacterBaseStatsData, CharacterGenerationSpec, CharacterMetaAttributesData

# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore

# <<< ИЗМЕНЕНО: Импортируем обновленный хелпер статусов
from .handler_utils.redis_task_status_handler import set_task_final_status

from .handler_utils.character_meta_handler import get_character_meta_attributes
from .handler_utils.character_stats_generator import generate_generated_base_stats
from .handler_utils.character_cache_handlers import (
    get_character_personality_id_from_cache,
    get_character_background_id_from_cache,
)


class CharacterBatchProcessor:
    """
    Оркестратор для обработки батчей генерации персонажей.
    Использует новую архитектуру с RedisBatchStore.
    """
    # <<< ИЗМЕНЕНО: Конструктор упрощен и обновлен
    def __init__(
        self,
        repository_manager: RepositoryManager,
        redis_batch_store: RedisBatchStore,
        reference_data_reader: ReferenceDataReader,
    ):
        self.repository_manager = repository_manager
        self.redis_batch_store = redis_batch_store
        self.reference_data_reader = reference_data_reader
        self.logger = logger
        self.char_pool_repo: ICharacterPoolRepository = self.repository_manager.character_pools
        logger.info("CharacterBatchProcessor (v2, RedisBatchStore) инициализирован.")

    async def process_batch(
        self,
        redis_worker_batch_id: str,
        task_key_template: str,
        batch_specs: List[CharacterGenerationSpec]
    ) -> None:
        """
        Основной метод для обработки одного батча задач генерации персонажей.
        """
        log_prefix = f"CHAR_BATCH_PROC_ID({redis_worker_batch_id}):"
        self.logger.info(f"{log_prefix} Начало обработки батча.")

        if not batch_specs:
            self.logger.info(f"{log_prefix} Батч не содержит спецификаций. Завершаем как пустой.")
            # <<< ИЗМЕНЕНО: Передаем redis_batch_store
            await set_task_final_status(
                redis_worker_batch_id, task_key_template, status="completed",
                final_generated_count=0, target_count=0, was_empty=True,
                redis_batch_store=self.redis_batch_store,
            )
            return

        target_count = len(batch_specs)
        generated_character_data_for_db: List[Dict[str, Any]] = []
        error_count = 0

        for spec in batch_specs:
            try:
                core_attributes_dto = generate_generated_base_stats(spec.quality_level)
                meta_attributes_dto = await get_character_meta_attributes(spec.quality_level)
                first_name, last_name = NameOrchestrator.generate_character_name(gender=spec.gender)
                personality_id = await get_character_personality_id_from_cache(self.reference_data_reader)
                background_story_id = await get_character_background_id_from_cache(self.reference_data_reader)

                pool_entry_data = {
                    "creature_type_id": spec.creature_type_id,
                    "gender": spec.gender,
                    "quality_level": spec.quality_level,
                    "base_stats": core_attributes_dto.model_dump(),
                    "initial_role_name": "UNASSIGNED_ROLE",
                    "initial_skill_levels": {},
                    "name": first_name,
                    "surname": last_name,
                    "personality_id": personality_id,
                    "background_story_id": background_story_id,
                    "visual_appearance_data": {},
                    "is_unique": meta_attributes_dto.is_unique,
                    "rarity_score": meta_attributes_dto.rarity_score,
                    "status": "available",
                }
                generated_character_data_for_db.append(pool_entry_data)
            except Exception as e:
                self.logger.error(f"{log_prefix} Ошибка при генерации одного персонажа: {e}", exc_info=True)
                error_count += 1
        
        generated_count = 0
        if generated_character_data_for_db:
            try:
                self.logger.info(f"{log_prefix} Попытка пакетного сохранения {len(generated_character_data_for_db)} персонажей в БД.")
                generated_count = await self.char_pool_repo.upsert_many(generated_character_data_for_db)
                self.logger.info(f"{log_prefix} Успешно сохранено {generated_count} персонажей в БД.")
            except Exception as db_e:
                self.logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Не удалось выполнить пакетное сохранение: {db_e}", exc_info=True)
                error_count = target_count
                generated_count = 0
                raise RuntimeError(f"Ошибка пакетного сохранения персонажей в БД: {db_e}") from db_e

        final_generated_count = generated_count
        final_status = "completed"
        error_message = None

        if error_count > 0 or final_generated_count < target_count:
            final_status = "completed_with_warnings"
            error_message = f"{error_count} ошибок. Сгенерировано: {final_generated_count}/{target_count}."
        
        if final_generated_count == 0 and error_count > 0:
            final_status = "failed"
            error_message = "Все персонажи в батче не сгенерированы из-за ошибок."

        # <<< ИЗМЕНЕНО: Передаем redis_batch_store
        await set_task_final_status(
            redis_worker_batch_id, task_key_template, status=final_status,
            final_generated_count=final_generated_count, target_count=target_count,
            error_message=error_message,
            redis_batch_store=self.redis_batch_store,
        )
        
        self.logger.info(f"{log_prefix} Обработка батча завершена. Сгенерировано: {final_generated_count}/{target_count}. Статус: {final_status}.")
