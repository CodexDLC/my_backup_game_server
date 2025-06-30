# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_character/character_template_planner.py
import uuid
from typing import List, Dict, Any, Optional
from collections import Counter

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.template_generator_character.pre_process.character_batch_generator import generate_pre_batch_from_pool_needs
from game_server.config.settings.character.generator_settings import CHARACTER_TEMPLATE_QUALITY_CONFIG, TARGET_POOL_QUALITY_DISTRIBUTION
from game_server.config.settings.process.prestart import CHARACTER_POOL_TARGET_SIZE
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches
from game_server.config.provider import config
from game_server.common_contracts.dtos.orchestrator_dtos import CharacterGenerationSpec
from game_server.config.constants.redis_key.task_keys import KEY_CHARACTER_GENERATION_TASK

# 🔥 ИЗМЕНЕНИЕ: Импортируем RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore


class CharacterTemplatePlanner:
    def __init__(
        self,
        repository_manager: RepositoryManager,
        # 🔥 ИЗМЕНЕНИЕ: Зависимость заменена на RedisBatchStore
        redis_batch_store: RedisBatchStore,
        pool_target_size: int = CHARACTER_POOL_TARGET_SIZE,
    ):
        self.repository_manager = repository_manager
        self.pool_target_size = pool_target_size
        # 🔥 ИЗМЕНЕНИЕ: Сохраняем новую зависимость
        self.redis_batch_store = redis_batch_store
        self.logger = logger
        logger.debug(f"CharacterTemplatePlanner (v2) инициализирован. Целевой размер пула: {self.pool_target_size}")

    async def _get_pool_analysis_data(self) -> tuple[int, Counter, Counter]:
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
        logger.debug("Запуск pre_process для CharacterTemplatePlanner...")
        current_target_pool_size = target_pool_total_size_override if target_pool_total_size_override is not None else self.pool_target_size
        
        current_pool_count, current_gender_counts_in_pool, current_quality_counts_in_pool = await self._get_pool_analysis_data()
        
        num_to_generate_overall = max(0, current_target_pool_size - current_pool_count)

        if num_to_generate_overall <= 0:
            logger.debug(f"Пул персонажей ({current_pool_count}/{current_target_pool_size}) не требует пополнения.")
            return []
        
        logger.info(f"Требуется спланировать {num_to_generate_overall} персонажей.")

        full_pre_batch_specs_list: List[CharacterGenerationSpec] = await generate_pre_batch_from_pool_needs(
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
            return []
        
        logger.info(f"Сформирован список из {len(full_pre_batch_specs_list)} спецификаций для генерации персонажей.")

        character_generation_tasks: List[Dict[str, Any]] = []
        
        character_chunks = list(split_into_batches(full_pre_batch_specs_list, config.settings.prestart.CHARACTER_GENERATION_MAX_BATCH_SIZE))
        logger.info(f"Спецификации персонажей разделены на {len(character_chunks)} батчей.")

        for chunk_of_specs_objs in character_chunks:
            if not chunk_of_specs_objs:
                continue
            
            chunk_of_specs_as_dicts = [spec_obj.model_dump(by_alias=True) for spec_obj in chunk_of_specs_objs]
            redis_worker_batch_id = str(uuid.uuid4())

            # 🔥 ИЗМЕНЕНИЕ: Используем RedisBatchStore для сохранения данных задачи
            batch_data_to_save = {
                "specs": chunk_of_specs_as_dicts,
                "target_count": len(chunk_of_specs_as_dicts),
                "status": "pending"
            }

            success_save = await self.redis_batch_store.save_batch(
                key_template=KEY_CHARACTER_GENERATION_TASK,  # <<< ДОБАВЛЕНО
                batch_id=redis_worker_batch_id,
                batch_data=batch_data_to_save,
                ttl_seconds=config.settings.redis.BATCH_TASK_TTL_SECONDS
            )

            if success_save:
                character_generation_tasks.append({"batch_id": redis_worker_batch_id})
                self.logger.info(f"Батч ID '{redis_worker_batch_id}' (персонажи) сохранен в Redis.")
            else:
                self.logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' (персонажи) в Redis.")
        
        self.logger.info(f"Планировщик персонажей подготовил {len(character_generation_tasks)} батчей задач.")
        return character_generation_tasks
