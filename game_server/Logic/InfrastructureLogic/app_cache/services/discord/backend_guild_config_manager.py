# game_server\Logic\InfrastructureLogic\app_cache\services\discord\backend_guild_config_manager.py
import json
import logging
from typing import Dict, Any, Optional, List

import inject

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# 🔥 ИЗМЕНЕНИЕ: Импортируем наш новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_backend_guild_config import IBackendGuildConfigManager
from game_server.config.constants.redis_key.discord_keys import KEY_GUILD_CONFIG_HASH
from game_server.config.logging.logging_setup import app_logger as logger


# 🔥 ИЗМЕНЕНИЕ: Наследуемся от IBackendGuildConfigManager
class BackendGuildConfigManager(IBackendGuildConfigManager):
    """
    Менеджер кэша на стороне БЭКЕНДА для работы с копией конфигурации,
    полученной от Discord-бота.
    """
    @inject.autoparams()
    def __init__(self, redis_client: CentralRedisClient, logger: logging.Logger, ttl: int = -1):
        self.redis_client = redis_client
        self.logger = logger
        self.ttl = ttl
        self.KEY_PATTERN = KEY_GUILD_CONFIG_HASH
        self.logger.info("✨ BackendGuildConfigManager инициализирован.")
        
    async def _get_key(self, guild_id: int) -> str:
        """Формирует ключ Redis для Hash конфигурации гильдии."""
        return self.KEY_PATTERN.format(guild_id=guild_id)

    async def set_field(self, guild_id: int, field_name: str, data: Any) -> None:
        key = await self._get_key(guild_id)
        try:
            value = json.dumps(data) if isinstance(data, (dict, list)) else data
            await self.redis_client.hset(key, field_name, value)
            if self.ttl > 0:
                await self.redis_client.expire(key, self.ttl)
        except Exception as e:
            logger.error(f"Ошибка при установке поля '{field_name}' в Hash '{key}': {e}", exc_info=True)
            raise

    async def get_field(self, guild_id: int, field_name: str) -> Optional[Any]:
        key = await self._get_key(guild_id)
        try:
            value = await self.redis_client.hget(key, field_name)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении поля '{field_name}' из Hash '{key}': {e}", exc_info=True)
            raise
            
    # 🔥 ИЗМЕНЕНИЕ: Добавлены остальные методы для соответствия интерфейсу
    async def get_all_fields(self, guild_id: int) -> Optional[Dict[str, Any]]:
        key = await self._get_key(guild_id)
        try:
            all_data = await self.redis_client.hgetall(key)
            if not all_data:
                return None
            
            parsed_data = {}
            for field, value in all_data.items():
                try:
                    parsed_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[field] = value
            return parsed_data
        except Exception as e:
            logger.error(f"Ошибка при получении всех полей из Hash '{key}': {e}", exc_info=True)
            raise

    async def delete_fields(self, guild_id: int, fields: List[str]) -> None:
        if not fields:
            return
        key = await self._get_key(guild_id)
        try:
            await self.redis_client.hdel(key, *fields)
        except Exception as e:
            logger.error(f"Ошибка при удалении полей {fields} из Hash '{key}': {e}", exc_info=True)
            raise

    async def delete_config(self, guild_id: int) -> None:
        key = await self._get_key(guild_id)
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Ошибка при удалении Hash '{key}': {e}", exc_info=True)
            raise