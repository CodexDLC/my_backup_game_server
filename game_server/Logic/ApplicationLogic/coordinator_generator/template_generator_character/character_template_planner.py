# game_server/Logic/ApplicationLogic/coordinator_generator/template_generator_character/character_template_planner.py

import uuid
from typing import List, Dict, Any, Callable, Coroutine, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from collections import Counter

# --- Логгер ---
from game_server.Logic.ApplicationLogic.coordinator_generator.generator_settings import CHARACTER_POOL_TARGET_SIZE
from game_server.services.logging.logging_setup import logger

# --- Импорты ---
from game_server.Logic.ApplicationLogic.coordinator_generator.template_generator_character.pre_process.character_batch_generator import generate_pre_batch_from_pool_needs
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_character import CHARACTER_TEMPLATE_QUALITY_CONFIG, TARGET_POOL_QUALITY_DISTRIBUTION
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.ORM_character_pool_manager import CharacterPoolRepository

# БЫЛО: from ... import CentralCentralRedisClient
# СТАЛО: Импорт удален, так как он больше не нужен.

class CharacterTemplatePlanner:
    """
    Управляет процессом генерации шаблонов персонажей.
    """
    def __init__(
        self,
        async_session_factory: Callable[[], AsyncSession] = AsyncSessionLocal,
        pool_target_size: int = CHARACTER_POOL_TARGET_SIZE,
    ):
        """Конструктор больше не принимает и не зависит от Redis."""
        # БЫЛО: redis_client: CentralCentralRedisClient, ...
        # СТАЛО: Параметр redis_client полностью удален.
        self.async_session_factory = async_session_factory
        self.pool_target_size = pool_target_size
        logger.info(f"CharacterTemplateGenerator инициализирован. Целевой размер пула: {self.pool_target_size}")

    # Все остальные методы остаются без изменений, так как они не использовали Redis.
    async def _get_pool_analysis_data(self, session: AsyncSession) -> Tuple[int, Counter, Counter]:
        repo = CharacterPoolRepository(session)
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
        logger.info("Запуск pre_process для CharacterTemplateGenerator (только планирование)...")
        current_target_pool_size = target_pool_total_size_override if target_pool_total_size_override is not None else self.pool_target_size
        
        async with self.async_session_factory() as session:
            async with session.begin():
                current_pool_count, current_gender_counts_in_pool, current_quality_counts_in_pool = await self._get_pool_analysis_data(session)
        
        num_to_generate_overall = max(0, current_target_pool_size - current_pool_count)

        if num_to_generate_overall <= 0:
            logger.info(f"Пул персонажей ({current_pool_count}/{current_target_pool_size}) не требует пополнения. Генерация не запускается.")
            return []
        
        logger.info(f"Требуется спланировать {num_to_generate_overall} персонажей для достижения цели {current_target_pool_size} (текущее кол-во: {current_pool_count}).")

        full_pre_batch_specs = await generate_pre_batch_from_pool_needs(
            playable_races_data=playable_races_data,
            desired_gender_ratio=desired_gender_ratio,
            target_pool_total_size=current_target_pool_size,
            num_to_generate_for_batch=num_to_generate_overall,
            current_gender_counts_in_pool=current_gender_counts_in_pool,
            current_quality_counts_in_pool=current_quality_counts_in_pool,
            target_quality_distribution_config=TARGET_POOL_QUALITY_DISTRIBUTION,
            character_template_quality_config_param=CHARACTER_TEMPLATE_QUALITY_CONFIG
        )

        if not full_pre_batch_specs:
            logger.warning("Функция generate_pre_batch_from_pool_needs вернула пустой список спецификаций, хотя требовалась генерация.")
            return []
        
        logger.info(f"Сформирован полный предварительный список из {len(full_pre_batch_specs)} спецификаций для генерации персонажей.")
        return full_pre_batch_specs