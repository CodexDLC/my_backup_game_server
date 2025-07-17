# game_server/Logic/DomainLogic/worker_generator_templates/worker_character_template/handler_utils/character_cache_handlers.py

# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel


from game_server.config.provider import config
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.config.logging.logging_setup import app_logger as logger

# <<< ИЗМЕНЕНО: Импортируем константы напрямую из их нового местоположения
from game_server.config.constants.redis_key.reference_data_keys import (
    REDIS_KEY_GENERATOR_PERSONALITIES,
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES
)
from game_server.contracts.dtos.orchestrator.data_models import BackgroundStoryData, PersonalityData


PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel)

async def get_weighted_random_id_from_cached_hash(
    redis_key: str,
    id_field: str,
    weight_field: str,
    reference_data_reader: ReferenceDataReader,
    dto_type: Type[PydanticDtoType],
    default_id: Optional[int] = None
) -> Optional[int]:
    """
    Получает случайный ID с учетом веса, используя ReferenceDataReader.
    """
    selected_dto: Optional[PydanticDtoType] = await reference_data_reader.get_weighted_random_id(
        redis_key=redis_key,
        id_field=id_field,
        weight_field=weight_field,
        dto_type=dto_type,
        default_id=None
    )
    
    if selected_dto:
        selected_id = getattr(selected_dto, id_field, None)
        if selected_id is not None:
            try:
                return int(selected_id)
            except (ValueError, TypeError):
                logger.error(f"Невозможно преобразовать ID '{selected_id}' (из {id_field}) в int для ключа Redis '{redis_key}'.")
                return default_id
        return None
    
    return default_id


async def get_character_personality_id_from_cache(
    reference_data_reader: ReferenceDataReader
) -> int:
    """Выбирает ID личности из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        # <<< ИЗМЕНЕНО: Используем прямую константу
        redis_key=REDIS_KEY_GENERATOR_PERSONALITIES,
        id_field='personality_id',
        weight_field='rarity_weight',
        default_id=config.constants.character.DEFAULT_PERSONALITY_ID,
        reference_data_reader=reference_data_reader,
        dto_type=PersonalityData
    )
    return selected_id if selected_id is not None else config.constants.character.DEFAULT_PERSONALITY_ID


async def get_character_background_id_from_cache(
    reference_data_reader: ReferenceDataReader
) -> int:
    """Выбирает ID предыстории из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        # <<< ИЗМЕНЕНО: Используем прямую константу
        redis_key=REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
        id_field='story_id',
        weight_field='rarity_weight',
        default_id=config.constants.character.DEFAULT_BACKGROUND_STORY_ID,
        reference_data_reader=reference_data_reader,
        dto_type=BackgroundStoryData
    )
    return selected_id if selected_id is not None else config.constants.character.DEFAULT_BACKGROUND_STORY_ID


async def get_character_visual_data_placeholder() -> Dict[str, Any]:
    """(Без изменений) Возвращает заглушку для visual_appearance_data."""
    return {}
