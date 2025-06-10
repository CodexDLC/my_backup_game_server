# game_server/Logic/InfrastructureLogic/app_cache/services/character_cache_manager.py

import logging
from typing import Any, Dict, Optional

# Импортируем наш низкоуровневый клиент Redis с правильным именем
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client
# 🔥 ИЗМЕНЕНИЕ: Больше не нужен импорт CentralRedisClient для аннотаций в __init__
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient 

# Импортируем константы ключей и TTL для центрального Redis
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    KEY_PREFIX_CHARACTER_SNAPSHOT,
    KEY_PREFIX_ACCOUNT_BINDINGS,
    DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE,
    DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE,
    DEFAULT_TTL_ACCOUNT_BINDING
)

logger = logging.getLogger(__name__)

class CharacterCacheManager:
    """
    Высокоуровневый менеджер для кэширования и управления данными персонажей в Redis.
    Оперирует полными слепками персонажей и привязками Discord ID к Character ID.
    """
    # 🔥 ИЗМЕНЕНИЕ: Упрощаем __init__. Он больше не принимает внешний клиент.
    # Он всегда использует глобальный central_redis_client.
    def __init__(self):
        self.redis = central_redis_client
        logger.info("✅ CharacterCacheManager инициализирован.")

    # --- Методы для управления слепками персонажей ---
    async def get_character_snapshot(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает полный слепок персонажа из кэша Redis.
        Ключ: character:{character_id}
        """
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        snapshot = await self.redis.get_json(key)
        if snapshot:
            logger.debug(f"Получен снапшот персонажа {character_id} из Redis.")
        else:
            logger.debug(f"Снапшот персонажа {character_id} не найден в Redis.")
        return snapshot

    async def set_character_snapshot(self, character_id: str, snapshot_data: Dict[str, Any], is_online: bool = True):
        """
        Сохраняет или обновляет полный слепок персонажа в кэше Redis.
        TTL устанавливается в зависимости от онлайн-статуса персонажа.
        Ключ: character:{character_id}
        """
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        await self.redis.set_json(key, snapshot_data)
        
        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None:
            await self.redis.expire(key, ttl)
        logger.debug(f"Снапшот персонажа {character_id} сохранен/обновлен в Redis с TTL={ttl} (online={is_online}).")

    async def delete_character_snapshot(self, character_id: str):
        """
        Удаляет слепок персонажа из кэша Redis.
        Ключ: character:{character_id}
        """
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        await self.redis.delete(key)
        logger.info(f"Снапшот персонажа {character_id} удален из Redis.")

    async def update_character_snapshot_ttl(self, character_id: str, is_online: bool = True):
        """
        Обновляет TTL для существующего слепка персонажа.
        Используется для поддержания кэша "живым", пока персонаж онлайн.
        """
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None and await self.redis.exists(key):
            await self.redis.expire(key, ttl)
            logger.debug(f"TTL снапшота персонажа {character_id} обновлен до {ttl} (online={is_online}).")
        else:
            logger.debug(f"Не удалось обновить TTL снапшота персонажа {character_id} (ключ не найден или TTL None).")

    # --- Методы для управления привязками Discord ID к Character ID ---
    async def get_character_id_by_discord_id(self, discord_user_id: str) -> Optional[str]:
        """
        Получает Character ID по Discord User ID.
        Ключ: account_binding:discord:{discord_user_id}
        """
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        character_id = await self.redis.get(key)
        if character_id:
            logger.debug(f"Получен Character ID {character_id} для Discord User {discord_user_id}.")
        else:
            logger.debug(f"Character ID для Discord User {discord_user_id} не найден.")
        return character_id

    async def set_character_id_for_discord_id(self, discord_user_id: str, character_id: str, ttl_seconds: Optional[int] = DEFAULT_TTL_ACCOUNT_BINDING):
        """
        Сохраняет привязку Discord User ID к Character ID.
        Ключ: account_binding:discord:{discord_user_id}
        """
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        await self.redis.set(key, character_id)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.info(f"Привязка Discord User {discord_user_id} к Character {character_id} сохранена с TTL={ttl_seconds}.")

    async def delete_character_id_for_discord_id(self, discord_user_id: str):
        """
        Удаляет привязку Discord User ID к Character ID.
        """
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        await self.redis.delete(key)
        logger.info(f"Привязка Discord User {discord_user_id} удалена.")


# Создаем единственный экземпляр менеджера для использования в Backend'е
character_cache_manager = CharacterCacheManager()