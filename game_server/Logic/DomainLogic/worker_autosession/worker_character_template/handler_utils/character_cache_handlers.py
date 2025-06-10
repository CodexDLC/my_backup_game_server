# Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/character_cache_handlers.py

from typing import Dict, Any, Optional


# --- ИСПРАВЛЕННЫЙ ИМПОРТ ---
# 🔥 ИЗМЕНЕНИЕ: Теперь мы используем ТОЛЬКО reference_data_reader, так как нужный метод находится в нем.
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_reader import reference_data_reader

# Импортируем константы напрямую
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_generator import (
    DEFAULT_BACKGROUND_STORY_ID, DEFAULT_PERSONALITY_ID
)
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES, REDIS_KEY_GENERATOR_PERSONALITIES
)

async def get_weighted_random_id_from_cached_hash(
    redis_key: str,
    id_field: str,
    weight_field: str,
    default_id: Optional[int] = None
) -> Optional[int]:
    """
    Получает случайный ID с учетом веса, используя ReferenceDataReader.
    """
    # 🔥 ИЗМЕНЕНИЕ: Вызов идет к правильному объекту, который мы импортировали выше.
    return await reference_data_reader.get_weighted_random_id(
        redis_key=redis_key,
        id_field=id_field,
        weight_field=weight_field,
        default_id=default_id
    )

async def get_character_personality_id_from_cache() -> int:
    """Выбирает ID личности из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        redis_key=REDIS_KEY_GENERATOR_PERSONALITIES, 
        id_field='personality_id',
        weight_field='rarity_weight',
        default_id=DEFAULT_PERSONALITY_ID
    )
    return selected_id if selected_id is not None else DEFAULT_PERSONALITY_ID

async def get_character_background_id_from_cache() -> int:
    """Выбирает ID предыстории из кэша Redis."""
    selected_id = await get_weighted_random_id_from_cached_hash(
        redis_key=REDIS_KEY_GENERATOR_BACKGROUND_STORIES, 
        id_field='story_id',
        weight_field='rarity_weight',
        default_id=DEFAULT_BACKGROUND_STORY_ID
    )
    return selected_id if selected_id is not None else DEFAULT_BACKGROUND_STORY_ID

async def get_character_visual_data_placeholder() -> Dict[str, Any]:
    """(Без изменений) Возвращает заглушку для visual_appearance_data."""
    return {}
