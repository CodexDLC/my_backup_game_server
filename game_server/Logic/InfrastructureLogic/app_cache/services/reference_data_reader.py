# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data_reader.py

import json
import random
from typing import Dict, Any, Optional, List

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client 
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    REDIS_KEY_GENERATOR_ITEM_BASE,
    REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_SUFFIXES,
    REDIS_KEY_GENERATOR_MODIFIERS,
    REDIS_KEY_GENERATOR_SKILLS,
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
    REDIS_KEY_GENERATOR_PERSONALITIES,
    REDIS_KEY_GENERATOR_INVENTORY_RULES,
)
from game_server.services.logging.logging_setup import logger

class ReferenceDataReader:
    """
    Читает справочные данные генераторов из Redis.
    """
    def __init__(self):
        self.redis = central_redis_client

    async def _get_full_hash_as_dict(self, redis_key: str) -> Dict[str, Any]:
        try:
            raw_hash = await self.redis.hgetall(redis_key) 
            parsed_dict = {}
            for field, value in raw_hash.items(): 
                try:
                    parsed_dict[field] = json.loads(value)
                except json.JSONDecodeError as e:
                    logger.critical(f"JSONDecodeError при парсинге поля '{field}' в хеше '{redis_key}': {e}.")
                    raise 
            return parsed_dict
        except Exception as e:
            logger.error(f"Ошибка при чтении хеша '{redis_key}' из Redis: {e}", exc_info=True)
            return {}

    # 🔥 ИЗМЕНЕНИЕ: Метод get_weighted_random_id ПЕРЕМЕЩЕН сюда. Это его правильное место.
    async def get_weighted_random_id(
        self, 
        redis_key: str, 
        id_field: str, 
        weight_field: str, 
        default_id: Optional[int]
    ) -> Optional[int]:
        """
        Получает данные из Redis HASH, делает случайный выбор ID с учетом веса.
        """
        try:
            data_dict = await self._get_full_hash_as_dict(redis_key)
            if not data_dict:
                logger.warning(f"Кэш для ключа '{redis_key}' пуст или не найден.")
                return default_id

            choices = []
            weights = []
            
            for item_data in data_dict.values():
                item_id = item_data.get(id_field)
                if item_id is None or not isinstance(item_id, (int, float)):
                    continue

                try:
                    item_weight = float(item_data.get(weight_field, 1.0))
                except (ValueError, TypeError):
                    item_weight = 1.0
                
                if item_weight >= 0:
                    choices.append(int(item_id))
                    weights.append(item_weight)

            if not choices:
                logger.warning(f"Не найдено подходящих вариантов для выбора в кэше '{redis_key}'.")
                return default_id

            return random.choices(choices, weights=weights, k=1)[0]

        except Exception as e:
            logger.error(f"Ошибка при взвешенном выборе из кэша '{redis_key}': {e}", exc_info=True)
            return default_id

    # --- Остальные методы чтения ---
    async def get_all_item_bases(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_ITEM_BASE)

    async def get_all_materials(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_MATERIALS)

    async def get_all_suffixes(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_SUFFIXES)

    async def get_all_modifiers(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_MODIFIERS)

    async def get_all_skills(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_SKILLS)

    async def get_all_background_stories(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_BACKGROUND_STORIES)

    async def get_all_personalities(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_PERSONALITIES)

    async def get_all_inventory_rules(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_INVENTORY_RULES)

# Создаем единственный экземпляр менеджера для использования в Backend'е
reference_data_reader = ReferenceDataReader()
