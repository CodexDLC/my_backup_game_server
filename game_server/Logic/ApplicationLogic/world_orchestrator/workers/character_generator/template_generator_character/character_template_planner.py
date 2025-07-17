# game_server/Logic/ApplicationLogic/world_orchestrator/workers/character_generator/template_generator_character/character_template_planner.py

import uuid
import logging
import inject
from typing import List, Dict, Any, Optional, Callable
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.contracts.dtos.orchestrator.data_models import CharacterGenerationSpec

# Импортируем утилиты и DTO
from .pre_process.character_batch_generator import generate_pre_batch_from_pool_needs
from game_server.Logic.InfrastructureLogic.arq_worker.utils.task_batch_dispatcher import split_into_batches


# Импортируем зависимости, которые будем внедрять через DI
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# 👇 ШАГ 1: ПРЯМОЙ ИМПОРТ КОНСТАНТ
from game_server.config.constants.arq import KEY_CHARACTER_GENERATION_TASK
from game_server.config.settings.process.prestart import (
    CHARACTER_POOL_TARGET_SIZE,
    CHARACTER_GENERATION_MAX_BATCH_SIZE,
  
)
from game_server.config.settings.redis_setting import BATCH_TASK_TTL_SECONDS
from game_server.config.settings.character.generator_settings import (
    TARGET_POOL_QUALITY_DISTRIBUTION,
    CHARACTER_TEMPLATE_QUALITY_CONFIG
)


class CharacterTemplatePlanner:
    """
    Планирует создание шаблонов персонажей. Работает в рамках транзакции.
    """
    # 👇 ШАГ 2: В __init__ ОСТАВЛЯЕМ ТОЛЬКО ВНЕДРЯЕМЫЕ ЗАВИСИМОСТИ
    # Обратите внимание: мы внедряем фабрики репозиториев и сессий
    @inject.autoparams(
        'logger',
        'char_pool_repo_factory',
        'redis_batch_store'
    )
    def __init__(
        self,
        logger: logging.Logger,
        char_pool_repo_factory: Callable[[AsyncSession], ICharacterPoolRepository],
        redis_batch_store: RedisBatchStore
    ):
        self.logger = logger
        # self._session_factory больше не нужен
        self._char_pool_repo_factory = char_pool_repo_factory
        self.redis_batch_store = redis_batch_store

        # 👇 ШАГ 3: ПРИСВАИВАЕМ КОНСТАНТЫ, ПОЛУЧЕННЫЕ ЧЕРЕЗ ИМПОРТ
        self.pool_target_size = CHARACTER_POOL_TARGET_SIZE
        self.max_batch_size = CHARACTER_GENERATION_MAX_BATCH_SIZE
        self.batch_ttl = BATCH_TASK_TTL_SECONDS
        self.target_quality_distribution = TARGET_POOL_QUALITY_DISTRIBUTION
        self.character_template_quality_config = CHARACTER_TEMPLATE_QUALITY_CONFIG

        self.logger.debug(f"CharacterTemplatePlanner инициализирован. Целевой размер пула: {self.pool_target_size}")

    # 👇 ШАГ 4: ДЕЛАЕМ ГЛАВНЫЙ МЕТОД ТРАНЗАКЦИОННЫМ
    @transactional(AsyncSessionLocal)
    async def pre_process(
        self,
        session: AsyncSession, # <-- Метод теперь принимает сессию
        playable_races_data: List[Dict[str, Any]],
        desired_gender_ratio: float,
        target_pool_total_size_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Главный метод, координирующий планирование. Выполняется в рамках одной транзакции.
        """
        self.logger.debug("Запуск pre_process для CharacterTemplatePlanner...")
        current_target_pool_size = target_pool_total_size_override if target_pool_total_size_override is not None else self.pool_target_size

        # Создаем репозиторий с активной сессией
        char_pool_repo = self._char_pool_repo_factory(session)
        
        current_pool_count, current_gender_counts, current_quality_counts = await self._get_pool_analysis_data(char_pool_repo)

        num_to_generate_overall = max(0, current_target_pool_size - current_pool_count)

        if num_to_generate_overall <= 0:
            self.logger.debug(f"Пул персонажей ({current_pool_count}/{current_target_pool_size}) не требует пополнения.")
            return []

        self.logger.info(f"Требуется спланировать {num_to_generate_overall} персонажей.")

        specs_list = await generate_pre_batch_from_pool_needs(
            playable_races_data=playable_races_data,
            desired_gender_ratio=desired_gender_ratio,
            target_pool_total_size=current_target_pool_size,
            num_to_generate_for_batch=num_to_generate_overall,
            current_gender_counts_in_pool=current_gender_counts,
            current_quality_counts_in_pool=current_quality_counts,
            target_quality_distribution_config=self.target_quality_distribution,
            character_template_quality_config_param=self.character_template_quality_config
        )

        if not specs_list:
            return []

        return await self._save_specs_as_batches(specs_list)

    async def _get_pool_analysis_data(self, char_pool_repo: ICharacterPoolRepository) -> tuple[int, Counter, Counter]:
        """Анализирует текущее состояние пула персонажей в БД."""
        all_chars = await char_pool_repo.get_all_characters()
        available_chars = [char for char in all_chars if getattr(char, 'status', 'available') == 'available']
        
        current_total = len(available_chars)
        gender_counts = Counter(getattr(char, 'gender', '').upper() for char in available_chars if getattr(char, 'gender'))
        quality_counts = Counter(getattr(char, 'quality_level') for char in available_chars if hasattr(char, 'quality_level'))

        self.logger.debug(f"Анализ пула: {current_total} доступных, гендеры: {gender_counts}, качества: {quality_counts}")
        return current_total, gender_counts, quality_counts

    async def _save_specs_as_batches(self, specs_list: List[CharacterGenerationSpec]) -> List[Dict[str, Any]]:
        """
        Разделяет список спецификаций на батчи и сохраняет их в Redis.
        """
        self.logger.info(f"Сформирован список из {len(specs_list)} спецификаций. Сохранение в Redis...")
        
        character_chunks = list(split_into_batches(specs_list, self.max_batch_size))
        self.logger.info(f"Спецификации разделены на {len(character_chunks)} батчей.")

        tasks_for_arq = []
        for chunk in character_chunks:
            if not chunk: continue
            batch_id = str(uuid.uuid4())
            batch_data = {
                "specs": [spec.model_dump(by_alias=True) for spec in chunk],
                "target_count": len(chunk), "status": "pending"
            }
            was_saved = await self.redis_batch_store.save_batch(
                key_template=KEY_CHARACTER_GENERATION_TASK,
                batch_id=batch_id, batch_data=batch_data, ttl_seconds=self.batch_ttl
            )
            if was_saved:
                tasks_for_arq.append({"batch_id": batch_id})
                self.logger.info(f"Батч ID '{batch_id}' (персонажи) сохранен в Redis.")
            else:
                self.logger.error(f"Не удалось сохранить батч ID '{batch_id}' (персонажи) в Redis.")
        
        self.logger.info(f"Планировщик персонажей подготовил {len(tasks_for_arq)} батчей задач.")
        return tasks_for_arq