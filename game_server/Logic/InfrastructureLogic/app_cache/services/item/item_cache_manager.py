# game_server/Logic/InfrastructureLogic/app_cache/services/item/item_cache_manager.py

import logging
from typing import Any, Dict, Optional, List
import json
from abc import ABC, abstractmethod # Добавлено

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.constants.redis import KEY_PREFIX_ITEM_INSTANCE
from game_server.config.settings.redis_setting import DEFAULT_TTL_ITEM_INSTANCE_CACHE

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_item_cache import IItemCacheManager # Добавлено

logger = logging.getLogger(__name__)

# Изменяем класс ItemCacheManager, чтобы он наследовал от IItemCacheManager
class ItemCacheManager(IItemCacheManager): # Изменено
    """
    Высокоуровневый менеджер для кэширования и управления данными экземпляров предметов в Redis.
    Оперирует полными данными конкретных экземпляров предметов (например, item_instance:{item_uuid}).
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ ItemCacheManager инициализирован.")

    async def get_item_instance_data(self, item_uuid: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        item_data = await self.redis.get_json(key)
        if item_data:
            logger.debug(f"Получены данные экземпляра предмета {item_uuid} из Redis.")
        else:
            logger.debug(f"Данные экземпляра предмета {item_uuid} не найдены в Redis.")
        return item_data

    async def set_item_instance_data(self, item_uuid: str, item_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_ITEM_INSTANCE_CACHE):
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        await self.redis.set_json(key, item_data)

        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Данные экземпляра предмета {item_uuid} сохранены/обновлены в Redis с TTL={ttl_seconds}.")

    async def delete_item_instance_data(self, item_uuid: str):
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        await self.redis.delete(key)
        logger.info(f"Данные экземпляра предмета {item_uuid} удалены из Redis.")

    async def get_multiple_item_instances_data(self, item_uuids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        keys = [f"{KEY_PREFIX_ITEM_INSTANCE}:{uuid}" for uuid in item_uuids]
        results = await self.redis.mget(keys)

        items_map = {}
        for i, data in enumerate(results):
            if data:
                try:
                    items_map[item_uuids[i]] = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Ошибка декодирования JSON для item_uuid: {item_uuids[i]}. Данды: {data}")
                    items_map[item_uuids[i]] = None
            else:
                items_map[item_uuids[i]] = None
        logger.debug(f"Получены данные для {len(items_map)} из {len(item_uuids)} запрошенных предметов.")
        return items_map

# Удаляем глобальный экземпляр item_cache_manager, он будет инициализироваться в app_cache_initializer.py
# item_cache_manager: Optional['ItemCacheManager'] = None