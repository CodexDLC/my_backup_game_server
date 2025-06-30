# game_server/app_discord_bot/storage/cache/managers/guild_config_manager.py
import json
from typing import Dict, Any, Optional, List

from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager
from game_server.config.logging.logging_setup import app_logger as logger


class GuildConfigManager(IGuildConfigManager):
    """
    Менеджер кэша для хранения конфигурации гильдий (шардов) в виде Redis Hash.
    Предоставляет универсальные методы для работы с полями внутри этого Hash.
    """
    def __init__(self, redis_client: DiscordRedisClient, ttl: int = -1):
        """
        Инициализирует менеджер.
        Args:
            redis_client: Клиент для работы с Redis.
            ttl: Время жизни (в секундах) для всего Hash. -1 означает бессрочно.
        """
        self.redis_client = redis_client
        self.ttl = ttl
        self.KEY_PATTERN = RedisKeys.GUILD_CONFIG_HASH
        logger.info("✨ GuildConfigManager (v2-Hash) инициализирован.")

    async def _get_key(self, guild_id: int) -> str:
        """Формирует ключ Redis для Hash конфигурации гильдии."""
        return self.KEY_PATTERN.format(guild_id=guild_id)

    async def set_field(self, guild_id: int, field_name: str, data: Any) -> None:
        """
        Сохраняет или обновляет одно поле в Hash конфигурации гильдии.
        Сложные типы данных (dict, list) будут автоматически преобразованы в JSON.
        """
        key = await self._get_key(guild_id)
        try:
            value = json.dumps(data) if isinstance(data, (dict, list)) else data
            await self.redis_client.hset(key, field_name, value)
            logger.debug(f"Поле '{field_name}' в Hash '{key}' установлено.")
            
            # Если установлено время жизни, обновляем его для всего Hash
            if self.ttl > 0:
                await self.redis_client.expire(key, self.ttl)
        except Exception as e:
            logger.error(f"Ошибка при установке поля '{field_name}' в Hash '{key}': {e}", exc_info=True)

    async def get_field(self, guild_id: int, field_name: str) -> Optional[Any]:
        """
        Извлекает одно поле из Hash конфигурации гильдии.
        Автоматически пытается декодировать JSON-строки.
        """
        key = await self._get_key(guild_id)
        try:
            value = await self.redis_client.hget(key, field_name)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value # Возвращаем как есть, если это не JSON
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении поля '{field_name}' из Hash '{key}': {e}", exc_info=True)
            return None

    async def get_all_fields(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Извлекает все поля и их значения из Hash конфигурации гильдии.
        """
        key = await self._get_key(guild_id)
        try:
            all_data = await self.redis_client.hgetall(key)
            if not all_data:
                logger.warning(f"Конфигурация для гильдии {guild_id} (ключ {key}) не найдена в кэше.")
                return None
            
            # Декодируем значения из JSON там, где это возможно
            parsed_data = {}
            for field, value in all_data.items():
                try:
                    parsed_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[field] = value
            return parsed_data
        except Exception as e:
            logger.error(f"Ошибка при получении всех полей из Hash '{key}': {e}", exc_info=True)
            return None

    async def delete_fields(self, guild_id: int, fields: List[str]) -> None:
        """Удаляет одно или несколько полей из Hash."""
        if not fields:
            return
        key = await self._get_key(guild_id)
        try:
            await self.redis_client.hdel(key, *fields)
            logger.info(f"Поля {fields} удалены из Hash '{key}'.")
        except Exception as e:
            logger.error(f"Ошибка при удалении полей {fields} из Hash '{key}': {e}", exc_info=True)

    async def delete_config(self, guild_id: int) -> None:
        """Полностью удаляет Hash конфигурации для гильдии."""
        key = await self._get_key(guild_id)
        try:
            await self.redis_client.delete(key)
            logger.info(f"Конфигурация (Hash) для гильдии {guild_id} (ключ '{key}') удалена из кэша.")
        except Exception as e:
            logger.error(f"Ошибка при удалении Hash '{key}': {e}", exc_info=True)