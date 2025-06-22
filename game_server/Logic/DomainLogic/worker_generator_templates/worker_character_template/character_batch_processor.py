# game_server/Logic/DomainLogic/worker_generator_templates/worker_character_template/character_batch_processor.py

import logging
from typing import List, Dict, Any, Optional
from collections import Counter

# --- Логгер ---
from game_server.Logic.DomainLogic.worker_generator_templates.worker_character_template.handler_utils.character_stats_generator import generate_generated_base_stats
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Менеджеры и Хелперы ---
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.DomainLogic.worker_generator_templates.generator_name.name_orchestrator import NameOrchestrator
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from arq.connections import ArqRedis

# ДОБАВЛЕНО: Импорт CharacterPoolRepository interface (для типизации)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository

# Импортируем хелпер-функции статусов
from game_server.Logic.DomainLogic.worker_generator_templates.worker_character_template.handler_utils.redis_task_status_handler import set_task_final_status, update_task_generated_count

# --- Хендлеры из handler_utils ---

from .handler_utils.character_cache_handlers import (
    get_character_personality_id_from_cache,
    get_character_background_id_from_cache,
    get_character_visual_data_placeholder
)
from .handler_utils.character_meta_handler import get_character_meta_attributes

# ДОБАВЛЕНО: Импорт CharacterGenerationSpec DTO и CharacterBaseStatsData
from game_server.common_contracts.start_orcestrator.dtos import CharacterGenerationSpec, CharacterBaseStatsData
# ДОБАВЛЕНО: Импорт CharacterMetaAttributesData DTO
from game_server.common_contracts.start_orcestrator.dtos import CharacterMetaAttributesData


class CharacterBatchProcessor:
    """
    Оркестратор для обработки батчей генерации персонажей.
    Инкапсулирует логику, принимая зависимости через конструктор.
    """
    def __init__(
        self,
        repository_manager: RepositoryManager,
        task_queue_cache_manager: TaskQueueCacheManager,
        central_redis_client: CentralRedisClient,
        reference_data_reader: ReferenceDataReader,
        arq_redis_pool: ArqRedis, # ARQ Redis Pool
    ):
        self.repository_manager = repository_manager
        self.task_queue_cache_manager = task_queue_cache_manager
        self.central_redis_client = central_redis_client
        self.reference_data_reader = reference_data_reader
        self.arq_redis_pool = arq_redis_pool
        self.logger = logger
        self.char_pool_repo: ICharacterPoolRepository = self.repository_manager.character_pools

        logger.info("CharacterBatchProcessor инициализирован.")

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
            await set_task_final_status(
                redis_worker_batch_id, task_key_template, status="completed",
                final_generated_count=0, target_count=0, was_empty=True,
                task_queue_cache_manager=self.task_queue_cache_manager,
            )
            return

        target_count = len(batch_specs)
        
        generated_count = 0
        error_count = 0
        generated_character_data_for_db: List[Dict[str, Any]] = []

        for spec in batch_specs:
            self.logger.debug(f"{log_prefix} Попытка генерации персонажа: {spec}")

            try:
                gender = spec.gender
                quality_level = spec.quality_level
                creature_type_id = spec.creature_type_id

                core_attributes_dto: CharacterBaseStatsData = generate_generated_base_stats(
                    quality_level
                )
                
                # ИСПРАВЛЕНО: Доступ к данным DTO через model_dump()
                base_stats_dict = core_attributes_dto.model_dump()
                
                # Получаем мета-атрибуты, которые теперь также являются DTO
                meta_attributes_dto: CharacterMetaAttributesData = await get_character_meta_attributes(quality_level)

                # !!! ВАЖНО: Как я и упоминал ранее, generate_generated_base_stats
                # не возвращает initial_role_name или initial_skill_levels.
                # Вам нужно убедиться, что эти данные генерируются или получаются
                # другим способом, иначе они будут использовать дефолтные значения.
                # Я оставляю дефолтные значения пока, но это потенциальная точка для доработки.
                
                first_name, last_name = NameOrchestrator.generate_character_name(gender=gender)
                
                personality_id = await get_character_personality_id_from_cache(
                    reference_data_reader=self.reference_data_reader
                )
                background_story_id = await get_character_background_id_from_cache(
                    reference_data_reader=self.reference_data_reader
                )
                
                # visual_appearance_data = await get_character_visual_data_placeholder() # Закомментировано из-за возможных проблем с импортом

                pool_entry_data = {
                    "creature_type_id": creature_type_id,
                    "gender": gender,
                    "quality_level": quality_level,
                    "base_stats": base_stats_dict, # ИСПРАВЛЕНО: Используем словарь из DTO
                    "initial_role_name": "UNASSIGNED_ROLE", # Временное или дефолтное значение
                    "initial_skill_levels": {}, # Временное или дефолтное значение
                    "name": first_name,
                    "surname": last_name,
                    "personality_id": personality_id,
                    "background_story_id": background_story_id,
                    # "visual_appearance_data": visual_appearance_data, # Закомментировано, если функция не используется
                    "visual_appearance_data": {}, # Временное дефолтное значение
                    "is_unique": meta_attributes_dto.is_unique, # ИСПРАВЛЕНО: Доступ через точку
                    "rarity_score": meta_attributes_dto.rarity_score, # ИСПРАВЛЕНО: Доступ через точку
                    "status": "available",
                }
                
                generated_character_data_for_db.append(pool_entry_data)
                self.logger.debug(f"{log_prefix} Персонаж {pool_entry_data.get('name')} сгенерирован и добавлен в список для сохранения.")

            except Exception as e:
                self.logger.error(f"{log_prefix} Ошибка при генерации одного персонажа: {e}", exc_info=True)
                error_count += 1
                continue
        
        # Пакетное сохранение в БД
        if generated_character_data_for_db:
            try:
                self.logger.info(f"{log_prefix} Попытка пакетного сохранения {len(generated_character_data_for_db)} персонажей в БД.")
                # Предполагается, что upsert_many возвращает tuple (inserted_count, updated_count)
                # Если возвращает просто int (total_affected_rows), то нужно скорректировать
                inserted_count_or_total_affected = await self.char_pool_repo.upsert_many(generated_character_data_for_db)
                
                # Если upsert_many возвращает один int, используем его
                generated_count = inserted_count_or_total_affected 
                # Если upsert_many возвращает tuple (inserted, updated), то:
                # inserted, updated = inserted_count_or_total_affected
                # generated_count = inserted + updated

                self.logger.info(f"{log_prefix} Успешно сохранено {generated_count} персонажей в БД.") # Лог упрощен
                # Если нужно детализировать, убедитесь, что upsert_many возвращает inserted, updated
                # self.logger.info(f"{log_prefix} Успешно сохранено {generated_count} персонажей в БД (вставлено: {inserted}, обновлено: {updated}).")


            except Exception as db_e:
                self.logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Не удалось выполнить пакетное сохранение персонажей в БД: {db_e}", exc_info=True)
                error_count = target_count
                generated_count = 0
                raise RuntimeError(f"Ошибка пакетного сохранения персонажей в БД: {db_e}") from db_e
        else:
            self.logger.info(f"{log_prefix} Нет данных для сохранения в БД после генерации.")

        final_generated_count = generated_count
        
        self.logger.info(f"{log_prefix} Завершение цикла генерации. Всего ошибок: {error_count}. Сгенерировано: {final_generated_count}/{target_count}.")

        if error_count > 0 or final_generated_count != target_count:
            if final_generated_count == 0 and error_count > 0:
                final_status = "failed"
                error_message = f"Все ({error_count}) персонажи в батче не удалось сгенерировать/сохранить из-за ошибок."
            elif final_generated_count < target_count:
                final_status = "completed_with_warnings"
                error_message = f"{error_count} персонажей в батче не удалось сгенерировать/сохранить. Сгенегировано: {final_generated_count}/{target_count}. Не достигнут target_count."
            elif final_generated_count > target_count:
                final_status = "completed_with_warnings"
                error_message = f"Сгенегировано {final_generated_count} персонажей, но целевое количество {target_count}. Превышение целевого количества."
            else:
                final_status = "completed_with_warnings"
                error_message = f"{error_count} персонажей в батче не удалось сгенерировать/сохранить. Сгенегировано: {final_generated_count}/{target_count}."
        else:
            final_status = "completed"
            error_message = None

        await set_task_final_status(
            redis_worker_batch_id, task_key_template, status=final_status,
            final_generated_count=final_generated_count, target_count=target_count,
            error_message=error_message,
            task_queue_cache_manager=self.task_queue_cache_manager,
        )
        
        self.logger.info(f"{log_prefix} Обработка батча завершена. Сгенерировано: {final_generated_count}/{target_count}. Статус: {final_status}.")
