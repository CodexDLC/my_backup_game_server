# game_server/Logic/DomainLogic/worker_generator_templates/worker_character_template/handler_utils/character_cache_handlers.py

# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel

# 👇 ГЛАВНЫЙ ИМПОРТ: config provider
from game_server.config.provider import config

# Импорт класса ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорт DTO для Personality и BackgroundStory
from game_server.common_contracts.start_orcestrator.dtos import PersonalityData, BackgroundStoryData


# Определение TypeVar для Pydantic DTO (общий базовый класс для DTO)
PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel)

async def get_weighted_random_id_from_cached_hash(
    redis_key: str,
    id_field: str, # Имя поля, содержащего ID в DTO (например, 'personality_id')
    weight_field: str,
    reference_data_reader: ReferenceDataReader,
    dto_type: Type[PydanticDtoType],
    default_id: Optional[int] = None
) -> Optional[int]: # ИЗМЕНЕНО: Теперь возвращает Optional[int]
    """
    Получает случайный ID с учетом веса, используя ReferenceDataReader.
    ReferenceDataReader должен возвращать DTO объекты.
    """
    selected_dto: Optional[PydanticDtoType] = await reference_data_reader.get_weighted_random_id(
        redis_key=redis_key,
        id_field=id_field, # Эти поля будут использоваться для доступа к атрибутам DTO
        weight_field=weight_field, # Эти поля будут использоваться для доступа к атрибутам DTO
        dto_type=dto_type,
        default_id=None # default_id для ReferenceDataReader может быть None, т.к. DTO не имеет int ID
    )
    
    if selected_dto:
        # ИЗМЕНЕНО: Получаем атрибут и явно преобразуем его в int для гарантии
        # (хотя Pydantic DTO должен был уже обеспечить правильный тип).
        # Это защищает от случаев, когда данные могли быть неверно кэшированы как строки.
        selected_id = getattr(selected_dto, id_field, None)
        if selected_id is not None:
            try:
                return int(selected_id)
            except (ValueError, TypeError):
                logger.error(f"Невозможно преобразовать ID '{selected_id}' (из {id_field}) в int для ключа Redis '{redis_key}'.")
                # Если преобразование не удалось, можно вернуть default_id или None
                return default_id
        return None
    
    # Если DTO не выбран, возвращаем default_id (который уже int)
    return default_id


async def get_character_personality_id_from_cache(
    reference_data_reader: ReferenceDataReader
) -> int: # ИЗМЕНЕНО: Теперь возвращает int
    """Выбирает ID личности из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        redis_key=config.constants.redis.REDIS_KEY_GENERATOR_PERSONALITIES,
        id_field='personality_id', # ИСПРАВЛЕНО: Теперь ищем по 'personality_id'
        weight_field='rarity_weight',
        default_id=config.constants.character.DEFAULT_PERSONALITY_ID,
        reference_data_reader=reference_data_reader,
        dto_type=PersonalityData
    )
    # Возвращаем selected_id, если он не None, иначе используем значение по умолчанию.
    return selected_id if selected_id is not None else config.constants.character.DEFAULT_PERSONALITY_ID


async def get_character_background_id_from_cache(
    reference_data_reader: ReferenceDataReader
) -> int: # ИЗМЕНЕНО: Теперь возвращает int
    """Выбирает ID предыстории из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        redis_key=config.constants.redis.REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
        id_field='story_id', # ИСПРАВЛЕНО: Теперь ищем по 'story_id'
        weight_field='rarity_weight',
        default_id=config.constants.character.DEFAULT_BACKGROUND_STORY_ID,
        reference_data_reader=reference_data_reader,
        dto_type=BackgroundStoryData
    )
    # Возвращаем selected_id, если он не None, иначе используем значение по умолчанию.
    return selected_id if selected_id is not None else config.constants.character.DEFAULT_BACKGROUND_STORY_ID


async def get_character_visual_data_placeholder() -> Dict[str, Any]:
    """(Без изменений) Возвращает заглушку для visual_appearance_data."""
    return {}
