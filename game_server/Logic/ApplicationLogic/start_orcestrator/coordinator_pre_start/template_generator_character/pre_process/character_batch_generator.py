# Правильный путь: game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_character/pre_process/character_batch_generator.py

from typing import List, Dict, Any
from collections import Counter
# from sqlalchemy.ext.asyncio import AsyncSession # <- УДАЛЕНО

# Импорты утилит остаются
from .character_batch_utils import (
    determine_genders_for_batch,
    determine_qualities_for_batch,
    distribute_creature_types_for_batch
)

# ДОБАВЛЕНО: Импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорт CharacterGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import CharacterGenerationSpec #


async def generate_pre_batch_from_pool_needs(
    playable_races_data: List[Dict[str, Any]],
    desired_gender_ratio: float,
    target_pool_total_size: int,
    num_to_generate_for_batch: int,
    current_gender_counts_in_pool: Counter,
    current_quality_counts_in_pool: Counter,
    target_quality_distribution_config: Dict[str, float],
    character_template_quality_config_param: Dict[str, Any]
# ИЗМЕНЕНО: Сигнатура теперь возвращает List[CharacterGenerationSpec]
) -> List[CharacterGenerationSpec]:
    """
    Формирует "сырой" батч предварительных данных персонажей на основе переданных параметров.
    Возвращает список объектов CharacterGenerationSpec.
    """

    if num_to_generate_for_batch == 0:
        return []

    genders_for_batch = determine_genders_for_batch(
        num_to_generate_in_batch=num_to_generate_for_batch,
        current_gender_counts_in_pool=current_gender_counts_in_pool,
        target_pool_total_size=target_pool_total_size,
        desired_gender_ratio=desired_gender_ratio
    )

    qualities_for_batch = determine_qualities_for_batch(
        num_to_generate_in_batch=num_to_generate_for_batch,
        current_quality_counts_in_pool=current_quality_counts_in_pool,
        target_pool_total_size=target_pool_total_size,
        target_quality_distribution=target_quality_distribution_config,
        character_template_quality_config=character_template_quality_config_param
    )

    creature_types_for_batch = distribute_creature_types_for_batch(
        playable_races_data=playable_races_data,
        num_to_generate_in_batch=num_to_generate_for_batch
    )

    if not (len(genders_for_batch) == num_to_generate_for_batch and \
            len(qualities_for_batch) == num_to_generate_for_batch and \
            len(creature_types_for_batch) == num_to_generate_for_batch):
        logger.error(f"Критическая ошибка в generate_pre_batch_from_pool_needs: Не удалось сформировать корректные списки.")
        return []
        
    # ИЗМЕНЕНО: Теперь формируем список объектов CharacterGenerationSpec
    generated_pre_batch: List[CharacterGenerationSpec] = []
    for i in range(num_to_generate_for_batch):
        # Создаем DTO объект напрямую
        char_spec = CharacterGenerationSpec(
            gender=genders_for_batch[i],
            quality_level=qualities_for_batch[i],
            creature_type_id=creature_types_for_batch[i]
        )
        generated_pre_batch.append(char_spec)

    return generated_pre_batch