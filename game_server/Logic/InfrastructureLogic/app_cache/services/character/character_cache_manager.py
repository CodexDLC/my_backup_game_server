# game_server/Logic/InfrastructureLogic/app_cache/services/character/character_cache_manager.py

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod # Добавлено
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.constants.redis import KEY_CHARACTER_POOL_AVAILABLE_COUNT, KEY_PREFIX_ACCOUNT_BINDINGS, KEY_PREFIX_CHARACTER_SNAPSHOT
from game_server.config.settings.redis_setting import DEFAULT_TTL_ACCOUNT_BINDING, DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE, DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_character_cache import ICharacterCacheManager # Добавлено

logger = logging.getLogger(__name__)

# Изменяем класс CharacterCacheManager, чтобы он наследовал от ICharacterCacheManager
class CharacterCacheManager(ICharacterCacheManager): # Изменено
    """
    Высокоуровневый менеджер для кэширования и управления данными персонажей в Redis.
    Оперирует полными слепками персонажей и привязками Discord ID к Character ID.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ CharacterCacheManager инициализирован.")

    # --- Методы для управления слепками персонажей ---
    async def get_character_snapshot(self, character_id: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        snapshot = await self.redis.get_json(key)
        if snapshot:
            logger.debug(f"Получен снапшот персонажа {character_id} из Redis.")
        else:
            logger.debug(f"Снапшот персонажа {character_id} не найден в Redis.")
        return snapshot

    async def set_character_snapshot(self, character_id: str, snapshot_data: Dict[str, Any], is_online: bool = True):
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        await self.redis.set_json(key, snapshot_data)

        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None:
            await self.redis.expire(key, ttl)
        logger.debug(f"Снапшот персонажа {character_id} сохранен/обновлен в Redis с TTL={ttl} (online={is_online}).")

    async def delete_character_snapshot(self, character_id: str):
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        await self.redis.delete(key)
        logger.info(f"Снапшот персонажа {character_id} удален из Redis.")

    async def update_character_snapshot_ttl(self, character_id: str, is_online: bool = True):
        key = f"{KEY_PREFIX_CHARACTER_SNAPSHOT}:{character_id}"
        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None and await self.redis.exists(key):
            await self.redis.expire(key, ttl)
            logger.debug(f"TTL снапшота персонажа {character_id} обновлен до {ttl} (online={is_online}).")
        else:
            logger.debug(f"Не удалось обновить TTL снапшота персонажа {character_id} (ключ не найден или TTL None).")

    # --- Методы для управления привязками Discord ID к Character ID ---
    async def get_character_id_by_discord_id(self, discord_user_id: str) -> Optional[str]:
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        character_id = await self.redis.get(key)
        if character_id:
            logger.debug(f"Получен Character ID {character_id} для Discord User {discord_user_id}.")
        else:
            logger.debug(f"Character ID для Discord User {discord_user_id} не найден.")
        return character_id

    async def set_character_id_for_discord_id(self, discord_user_id: str, character_id: str, ttl_seconds: Optional[int] = DEFAULT_TTL_ACCOUNT_BINDING):
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        await self.redis.set(key, character_id)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.info(f"Привязка Discord User {discord_user_id} к Character {character_id} сохранена с TTL={ttl_seconds}.")

    async def delete_character_id_for_discord_id(self, discord_user_id: str):
        key = f"{KEY_PREFIX_ACCOUNT_BINDINGS}:discord:{discord_user_id}"
        await self.redis.delete(key)
        logger.info(f"Привязка Discord User {discord_user_id} удалена.")

    async def decrement_pool_count(self) -> int:
        new_count = await self.redis.decr(KEY_CHARACTER_POOL_AVAILABLE_COUNT)
        logger.info(f"Счетчик персонажей в пуле уменьшен. Новое значение: {new_count}")
        return new_count

    async def get_pool_count(self) -> int:
        count = await self.redis.get(KEY_CHARACTER_POOL_AVAILABLE_COUNT)
        return int(count) if count else 0

# Удаляем глобальный экземпляр character_cache_manager, он будет инициализироваться в app_cache_initializer.py
# character_cache_manager: Optional['CharacterCacheManager'] = None