# game_server/app_discord_bot/storage/cache/managers/player_session_manager.py

import json
import logging
import inject  # <-- 1. Добавьте этот импорт
from typing import Dict, Any, Optional

from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.constant.setting_manager import AuthTokenSettings
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.player_session_manager_interface import IPlayerSessionManager

class PlayerSessionManager(IPlayerSessionManager):
    """
    Менеджер кэша для хранения "живых" сессий игроков...
    """
    # 👇 2. Добавьте этот декоратор
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient, logger: logging.Logger, ttl: int = AuthTokenSettings.DEFAULT_TTL_SECONDS):
        self.redis_client = redis_client
        self.logger = logger
        self.ttl = ttl
        self.KEY_PATTERN = RedisKeys.CHARACTER_SESSION_HASH
        self.logger.info("✨ PlayerSessionManager инициализирован.")


    # 🔥 ИЗМЕНЕНИЕ: Ключ теперь зависит только от guild_id
    async def _get_key(self, guild_id: int) -> str:
        """Формирует ключ Redis для Hash'а сессий на шарде."""
        return self.KEY_PATTERN.format(guild_id=guild_id)

    # 🔥 ИЗМЕНЕНИЕ: Новый метод для сохранения/обновления сессии
    async def set_player_session(
        self, 
        guild_id: int, 
        account_id: int,
        session_data: Dict[str, Any]
    ) -> None:
        """
        Сохраняет или обновляет данные сессии для конкретного игрока.
        """
        key = await self._get_key(guild_id)
        # account_id теперь используется как имя поля в Hash
        field_name = str(account_id)
        try:
            await self.redis_client.hset(key, field_name, json.dumps(session_data))
            # При каждом обновлении сессии можно продлевать жизнь всего Hash
            if self.ttl > 0:
                await self.redis_client.expire(key, self.ttl)
            self.logger.debug(f"Сессия игрока {account_id} на шарде {guild_id} сохранена/обновлена.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении сессии игрока {account_id} на шарде {guild_id}: {e}", exc_info=True)

    # 🔥 ИЗМЕНЕНИЕ: Новый метод для получения сессии
    async def get_player_session(
        self, 
        guild_id: int, 
        account_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Извлекает данные сессии конкретного игрока.
        """
        key = await self._get_key(guild_id)
        field_name = str(account_id)
        try:
            data_str = await self.redis_client.hget(key, field_name)
            if data_str:
                return json.loads(data_str)
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка декодирования JSON для сессии игрока {account_id} на шарде {guild_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при извлечении сессии игрока {account_id} на шарде {guild_id}: {e}", exc_info=True)
            return None
            
    # 🔥 ИЗМЕНЕНИЕ: Новый метод для получения всех активных сессий на шарде
    async def get_all_sessions(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Извлекает все активные сессии на шарде."""
        key = await self._get_key(guild_id)
        try:
            all_sessions_str = await self.redis_client.hgetall(key)
            if not all_sessions_str:
                return {} # Возвращаем пустой словарь, если сессий нет
            
            # Декодируем каждую сессию из JSON
            all_sessions = {acc_id: json.loads(session_str) for acc_id, session_str in all_sessions_str.items()}
            return all_sessions
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех сессий с шарда {guild_id}: {e}", exc_info=True)
            return None

    # 🔥 ИЗМЕНЕНИЕ: Новый метод для удаления сессии (когда игрок выходит из игры)
    async def delete_player_session(
        self, 
        guild_id: int, 
        account_id: int
    ) -> None:
        """
        Удаляет данные сессии игрока из кэша.
        """
        key = await self._get_key(guild_id)
        field_name = str(account_id)
        try:
            await self.redis_client.hdel(key, field_name)
            self.logger.debug(f"Сессия игрока {account_id} на шарде {guild_id} удалена из кэша.")
        except Exception as e:
            self.logger.error(f"Ошибка при удалении сессии игрока {account_id} на шарде {guild_id}: {e}", exc_info=True)