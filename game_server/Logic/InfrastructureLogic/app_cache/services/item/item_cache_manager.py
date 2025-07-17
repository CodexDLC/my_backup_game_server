# game_server/Logic/InfrastructureLogic/app_cache/services/item/item_cache_manager.py

import logging
from typing import Any, Dict, Optional, List
import json
import inject # 🔥 ДОБАВЛЕНО: Импортируем inject

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.settings.redis_setting import DEFAULT_TTL_ITEM_INSTANCE_CACHE
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_item_cache import IItemCacheManager

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые, структурированные ключи
from game_server.config.constants.redis_key.item_keys import KEY_ITEM_INSTANCE_DATA, FIELD_ITEM_INSTANCE_DATA

logger = logging.getLogger(__name__)


class ItemCacheManager(IItemCacheManager):
    """
    Высокоуровневый менеджер для кэширования данных экземпляров предметов в Redis.
    Оперирует Hash-объектами для каждого экземпляра предмета.
    """
    # 🔥 ДОБАВЛЕНО: Декоратор @inject.autoparams()
    @inject.autoparams()
    def __init__(self, redis_client: CentralRedisClient, logger: logging.Logger):
        self.redis = redis_client
        self.logger = logger
        self.logger.info("✅ ItemCacheManager (v2) инициализирован.")

    async def get_item_instance_data(self, item_uuid: str) -> Optional[Dict[str, Any]]:
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон ключа
        key = KEY_ITEM_INSTANCE_DATA.format(item_uuid=item_uuid)
        # 🔥 ИЗМЕНЕНИЕ: Получаем конкретное поле 'data' из Hash
        item_data_str = await self.redis.hget(key, FIELD_ITEM_INSTANCE_DATA)
        
        if item_data_str:
            logger.debug(f"Получены данные экземпляра предмета {item_uuid} из Redis.")
            return json.loads(item_data_str)
        else:
            logger.debug(f"Данные экземпляра предмета {item_uuid} не найдены в Redis.")
            return None

    async def set_item_instance_data(self, item_uuid: str, item_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_ITEM_INSTANCE_CACHE):
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон ключа
        key = KEY_ITEM_INSTANCE_DATA.format(item_uuid=item_uuid)
        value = json.dumps(item_data)
        # 🔥 ИЗМЕНЕНИЕ: Сохраняем данные в поле 'data' внутри Hash
        await self.redis.hset(key, FIELD_ITEM_INSTANCE_DATA, value)

        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Данные экземпляра предмета {item_uuid} сохранены/обновлены в Redis с TTL={ttl_seconds}.")

    async def delete_item_instance_data(self, item_uuid: str):
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон ключа
        key = KEY_ITEM_INSTANCE_DATA.format(item_uuid=item_uuid)
        # Удаляем весь Hash, связанный с этим предметом
        await self.redis.delete(key)
        logger.info(f"Данные экземпляра предмета {item_uuid} (весь Hash) удалены из Redis.")

    async def get_multiple_item_instances_data(self, item_uuids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        # 🔥 ИЗМЕНЕНИЕ: Для эффективности используем pipeline, чтобы сделать несколько HGET за один запрос
        if not item_uuids:
            return {}

        pipe = self.redis.pipeline()
        for uuid in item_uuids:
            key = KEY_ITEM_INSTANCE_DATA.format(item_uuid=uuid)
            pipe.hget(key, FIELD_ITEM_INSTANCE_DATA)
        
        results = await pipe.execute()

        items_map = {}
        for i, data_str in enumerate(results):
            item_uuid = item_uuids[i]
            if data_str:
                try:
                    items_map[item_uuid] = json.loads(data_str)
                except (json.JSONDecodeError, TypeError):
                    logger.error(f"Ошибка декодирования JSON для item_uuid: {item_uuid}. Данные: {data_str}")
                    items_map[item_uuid] = None
            else:
                items_map[item_uuid] = None
        
        logger.debug(f"Получены данные для {len(items_map)} из {len(item_uuids)} запрошенных предметов.")
        return items_map
