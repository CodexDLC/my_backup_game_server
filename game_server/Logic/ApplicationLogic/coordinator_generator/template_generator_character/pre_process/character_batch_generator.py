# game_server/Logic/ApplicationLogic/coordinator_generator/character_template_generator/pre_process/character_batch_generator.py

from typing import List, Dict, Any
from collections import Counter
# sqlalchemy.ext.asyncio.AsyncSession может быть больше не нужна, если вся работа с БД вынесена
# from sqlalchemy.ext.asyncio import AsyncSession

# Импорты утилит остаются
from .character_batch_utils import (
    determine_genders_for_batch,
    determine_qualities_for_batch,
    distribute_creature_types_for_batch
)
# Константы теперь передаются как параметры

async def generate_pre_batch_from_pool_needs(
    # session: AsyncSession, # <- УДАЛИТЬ, если не используется для других целей
    # ИЗМЕНЕНИЕ СИГНАТУРЫ: теперь принимает playable_races_data
    playable_races_data: List[Dict[str, Any]], 
    desired_gender_ratio: float,
    target_pool_total_size: int, # Это current_target_pool_size из CharacterTemplateGenerator
    num_to_generate_for_batch: int, # Это num_to_generate_overall из CharacterTemplateGenerator
    current_gender_counts_in_pool: Counter,
    current_quality_counts_in_pool: Counter,
    target_quality_distribution_config: Dict[str, float], # Переданная TARGET_POOL_QUALITY_DISTRIBUTION
    character_template_quality_config_param: Dict[str, Any] # Переданная CHARACTER_TEMPLATE_QUALITY_CONFIG
) -> List[Dict[str, Any]]:
    """
    Формирует "сырой" батч предварительных данных персонажей на основе переданных параметров.
    (Обновленное описание)
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

    # ИЗМЕНЕНИЕ ВЫЗОВА: теперь передаем playable_races_data
    creature_types_for_batch = distribute_creature_types_for_batch(
        playable_races_data=playable_races_data, # ПЕРЕДАЕМ ВЕСЬ СПИСОК СЛОВАРЕЙ О РАСАХ
        num_to_generate_in_batch=num_to_generate_for_batch
    )

    if not (len(genders_for_batch) == num_to_generate_for_batch and \
            len(qualities_for_batch) == num_to_generate_for_batch and \
            len(creature_types_for_batch) == num_to_generate_for_batch):
        # logger.error(...) можно добавить, если логгер доступен и здесь
        # Убедитесь, что logger импортирован, если его нет
        # from game_server.services.logging.logging_setup import logger
        # logger.error(...)
        print(f"Критическая ошибка в generate_pre_batch_from_pool_needs: Не удалось сформировать корректные списки.")
        return []
        
    generated_pre_batch: List[Dict[str, Any]] = []
    for i in range(num_to_generate_for_batch):
        char_data = {
            "gender": genders_for_batch[i],
            "quality_level": qualities_for_batch[i],
            "creature_type_id": creature_types_for_batch[i]
        }
        generated_pre_batch.append(char_data)

    return generated_pre_batch