# game_server/Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/character_meta_handler.py

from typing import Dict, Any

# --- Логгер ---
from game_server.config.logging.logging_setup import app_logger as logger

# --- Константы через ConfigProvider ---
from game_server.common_contracts.dtos.orchestrator_dtos import CharacterMetaAttributesData
from game_server.config.provider import config

# ДОБАВЛЕНО: Импорт CharacterMetaAttributesData DTO



async def get_character_meta_attributes(
    quality_level: str,
) -> CharacterMetaAttributesData: # ИЗМЕНЕНО: Возвращает CharacterMetaAttributesData DTO
    """
    Определяет мета-атрибуты персонажа, такие как is_unique и rarity_score,
    получая необходимые конфигурации через ConfigProvider.
    Возвращает CharacterMetaAttributesData DTO.

    Args:
        quality_level (str): Уровень качества персонажа.

    Returns:
        CharacterMetaAttributesData: DTO с ключами "is_unique" (bool) и "rarity_score" (int).
    """

    highest_quality_level_name = config.constants.character.HIGHEST_QUALITY_LEVEL_NAME
    target_quality_distribution = config.settings.character.TARGET_POOL_QUALITY_DISTRIBUTION

    is_unique = (quality_level == highest_quality_level_name)

    percentage = target_quality_distribution.get(quality_level)

    if percentage is None:
        logger.warning(f"Мета-атрибуты: Качество '{quality_level}' не найдено в TARGET_POOL_QUALITY_DISTRIBUTION. Установлен rarity_score по умолчанию.")
        rarity_score = 100
    elif percentage <= 0:
        logger.warning(f"Мета-атрибуты: Недопустимый процент ({percentage}) для качества '{quality_level}'. Установлен очень высокий rarity_score.")
        rarity_score = 100000
    else:
        base_score = (1 / percentage)
        rarity_score = int(base_score * 100)

    # ИЗМЕНЕНО: Создаем и возвращаем CharacterMetaAttributesData DTO
    return CharacterMetaAttributesData(
        is_unique=is_unique,
        rarity_score=rarity_score
    )