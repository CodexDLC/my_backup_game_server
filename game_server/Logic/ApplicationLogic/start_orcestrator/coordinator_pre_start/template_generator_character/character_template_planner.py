# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_character/character_template_planner.py

import uuid
from typing import List, Dict, Any, Callable, Coroutine, Tuple, Optional
from collections import Counter
# from sqlalchemy.ext.asyncio import AsyncSession # УДАЛЕНО

# --- Логгер ---
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Импорты для зависимостей ---
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.template_generator_character.pre_process.character_batch_generator import generate_pre_batch_from_pool_needs
from game_server.config.settings.character.generator_settings import CHARACTER_TEMPLATE_QUALITY_CONFIG, TARGET_POOL_QUALITY_DISTRIBUTION
from game_server.config.settings.process.prestart import CHARACTER_POOL_TARGET_SIZE
from game_server.config.constants.redis import CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE

# Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # ДОБАВЛЕНО
# Импорт интерфейса CharacterPoolRepository для типизации
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository # ДОБАВЛЕНО

from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from arq.connections import ArqRedis

# Для утилиты разбиения на батчи
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches

# config provider
from game_server.config.provider import config

# ДОБАВЛЕНО: Импорт CharacterGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import CharacterGenerationSpec #


class CharacterTemplatePlanner:
    def __init__(
        self,
        repository_manager: RepositoryManager, # ИЗМЕНЕНО: теперь принимаем RepositoryManager
        task_queue_cache_manager: TaskQueueCacheManager,
        arq_redis_pool: ArqRedis,
        pool_target_size: int = CHARACTER_POOL_TARGET_SIZE,
    ):
        # УДАЛЕНО: self.async_session_factory = async_session_factory
        self.repository_manager = repository_manager # ДОБАВЛЕНО: сохраняем RepositoryManager
        self.pool_target_size = pool_target_size
        self.task_queue_cache_manager = task_queue_cache_manager
        self.arq_redis_pool = arq_redis_pool
        self.logger = logger
        logger.debug(f"CharacterTemplateGenerator инициализирован. Целевой размер пула: {self.pool_target_size}")


    async def _get_pool_analysis_data(self) -> Tuple[int, Counter, Counter]:
        repo: ICharacterPoolRepository = self.repository_manager.character_pools
        
        all_chars_from_db = await repo.get_all_characters()
        available_chars = [char for char in all_chars_from_db if getattr(char, 'status', 'available') == 'available']
        current_total_in_pool = len(available_chars)
        current_gender_counts = Counter(getattr(char, 'gender', '').upper() for char in available_chars if getattr(char, 'gender'))
        current_quality_counts = Counter(getattr(char, 'quality_level', None) for char in available_chars if getattr(char, 'quality_level'))
        if None in current_quality_counts:
            del current_quality_counts[None]
        logger.debug(f"Анализ пула: {current_total_in_pool} доступных, гендеры: {current_gender_counts}, качества: {current_quality_counts}")
        return current_total_in_pool, current_gender_counts, current_quality_counts

    async def pre_process(
        self,
        playable_races_data: List[Dict[str, Any]],
        desired_gender_ratio: float,
        target_pool_total_size_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        logger.debug("Запуск pre_process для CharacterTemplateGenerator (только планирование)...")
        current_target_pool_size = target_pool_total_size_override if target_pool_total_size_override is not None else self.pool_target_size
        
        current_pool_count, current_gender_counts_in_pool, current_quality_counts_in_pool = await self._get_pool_analysis_data()
        
        num_to_generate_overall = max(0, current_target_pool_size - current_pool_count)

        if num_to_generate_overall <= 0:
            logger.debug(f"Пул персонажей ({current_pool_count}/{current_target_pool_size}) не требует пополнения. Генерация не запускается.")
            return []
        
        logger.info(f"Требуется спланировать {num_to_generate_overall} персонажей для достижения цели {current_target_pool_size} (текущее кол-во: {current_pool_count}).")

        # ИЗМЕНЕНО: generate_pre_batch_from_pool_needs теперь возвращает List[CharacterGenerationSpec]
        full_pre_batch_specs_list: List[CharacterGenerationSpec] = await generate_pre_batch_from_pool_needs( #
            playable_races_data=playable_races_data,
            desired_gender_ratio=desired_gender_ratio,
            target_pool_total_size=current_target_pool_size,
            num_to_generate_for_batch=num_to_generate_overall,
            current_gender_counts_in_pool=current_gender_counts_in_pool,
            current_quality_counts_in_pool=current_quality_counts_in_pool,
            target_quality_distribution_config=TARGET_POOL_QUALITY_DISTRIBUTION,
            character_template_quality_config_param=CHARACTER_TEMPLATE_QUALITY_CONFIG
        )

        if not full_pre_batch_specs_list:
            logger.warning("Функция generate_pre_batch_from_pool_needs вернула пустой список спецификаций, хотя требовалась генерация.")
            return []
        
        logger.info(f"Сформирован полный предварительный список из {len(full_pre_batch_specs_list)} спецификаций для генерации персонажей.")

        character_generation_tasks: List[Dict[str, Any]] = []
        
        # split_into_batches теперь будет получать List[CharacterGenerationSpec]
        character_chunks = list(split_into_batches(full_pre_batch_specs_list, config.settings.prestart.CHARACTER_GENERATION_MAX_BATCH_SIZE)) #
        logger.info(f"Спецификации персонажей разделены на {len(character_chunks)} батчей размером до {config.settings.prestart.CHARACTER_GENERATION_MAX_BATCH_SIZE}.")

        for i, chunk_of_specs_objs in enumerate(character_chunks): # ИЗМЕНЕНО: переименовал переменную для ясности
            if not chunk_of_specs_objs:
                continue
            
            redis_worker_batch_id = str(uuid.uuid4())

            # ИЗМЕНЕНО: Преобразуем список CharacterGenerationSpec объектов в список словарей для Redis/JSON
            chunk_of_specs_as_dicts = [
                spec_obj.model_dump(by_alias=True) # ИСПОЛЬЗУЕМ Pydantic метод для преобразования в dict
                for spec_obj in chunk_of_specs_objs #
            ]

            logger.critical(f"*** DEBUG_ENQUEUE_CHAR_PRE: Batch ID='{redis_worker_batch_id}', Chunk Index={i+1}/{len(character_chunks)}, Chunk Size={len(chunk_of_specs_as_dicts)}")

            success_save = await self.task_queue_cache_manager.add_task_to_queue(
                batch_id=redis_worker_batch_id,
                key_template=CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                specs=chunk_of_specs_as_dicts, # Здесь все еще ожидаются словари, так как это данные для Redis/ARQ
                target_count=len(chunk_of_specs_as_dicts),
                initial_status="pending"
            )

            if success_save:
                character_generation_tasks.append({"batch_id": redis_worker_batch_id})
                logger.info(f"Батч ID '{redis_worker_batch_id}' успешно подготовлен и сохранен в Redis. Ожидает постановки в ARQ.")
            else:
                logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' (персонажи) в Redis. ARQ-задача не будет отправлена.")
        
        self.logger.info(f"Планировщик персонажей подготовил {len(character_generation_tasks)} батчей задач. Готов к постановке в очередь ARQ.")
        return character_generation_tasks