# game_server/Logic/InfrastructureLogic/app_cache/services/item_cache_manager.py

import logging
from typing import Any, Dict, Optional, List
import json 

# Импортируем низкоуровневый клиент Redis
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client

# Импортируем константы ключей и TTL для центрального Redis
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    KEY_PREFIX_ITEM_INSTANCE,
    DEFAULT_TTL_ITEM_INSTANCE_CACHE
)

logger = logging.getLogger(__name__)

class ItemCacheManager:
    """
    Высокоуровневый менеджер для кэширования и управления данными экземпляров предметов в Redis.
    Оперирует полными данными конкретных экземпляров предметов (например, item_instance:{item_uuid}).
    """
    # 🔥 ИЗМЕНЕНИЕ: Упрощаем __init__. Он больше не принимает внешний клиент.
    # Он всегда использует глобальный central_redis_client.
    def __init__(self):
        self.redis = central_redis_client
        logger.info("✅ ItemCacheManager инициализирован.")

    async def get_item_instance_data(self, item_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Получает полные данные экземпляра предмета из кэша Redis.
        Ключ: item_instance:{item_uuid}
        """
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        item_data = await self.redis.get_json(key)
        if item_data:
            logger.debug(f"Получены данные экземпляра предмета {item_uuid} из Redis.")
        else:
            logger.debug(f"Данные экземпляра предмета {item_uuid} не найдены в Redis.")
        return item_data

    async def set_item_instance_data(self, item_uuid: str, item_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_ITEM_INSTANCE_CACHE):
        """
        Сохраняет или обновляет полные данные экземпляра предмета в кэше Redis.
        Ключ: item_instance:{item_uuid}
        """
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        await self.redis.set_json(key, item_data)
        
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Данные экземпляра предмета {item_uuid} сохранены/обновлены в Redis с TTL={ttl_seconds}.")

    async def delete_item_instance_data(self, item_uuid: str):
        """
        Удаляет данные экземпляра предмета из кэша Redis.
        Ключ: item_instance:{item_uuid}
        """
        key = f"{KEY_PREFIX_ITEM_INSTANCE}:{item_uuid}"
        await self.redis.delete(key)
        logger.info(f"Данные экземпляра предмета {item_uuid} удалены из Redis.")

    async def get_multiple_item_instances_data(self, item_uuids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Получает данные нескольких экземпляров предметов за один запрос.
        """
        keys = [f"{KEY_PREFIX_ITEM_INSTANCE}:{uuid}" for uuid in item_uuids]
        results = await self.redis.mget(keys)

        items_map = {}
        for i, data in enumerate(results):
            if data:
                try:
                    items_map[item_uuids[i]] = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Ошибка декодирования JSON для item_uuid: {item_uuids[i]}. Данные: {data}")
                    items_map[item_uuids[i]] = None
            else:
                items_map[item_uuids[i]] = None
        logger.debug(f"Получены данные для {len(items_map)} из {len(item_uuids)} запрошенных предметов.")
        return items_map


# Создаем единственный экземпляр менеджера для использования в Backend'е
item_cache_manager = ItemCacheManager()