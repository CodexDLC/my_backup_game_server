# game_server/Logic/InfrastructureLogic/app_cache/services/character/character_cache_manager.py

import logging
import json
from typing import Any, Dict, Optional

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.settings.redis_setting import DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE, DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_character_cache import ICharacterCacheManager

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые, структурированные ключи
from game_server.config.constants.redis_key.character_keys import (
    KEY_CHARACTER_DATA,
    FIELD_CHARACTER_SNAPSHOT,
    KEY_WORLD_STATS,
    FIELD_CHARACTER_POOL_AVAILABLE
)

logger = logging.getLogger(__name__)


class CharacterCacheManager(ICharacterCacheManager):
    """
    Высокоуровневый менеджер для кэширования и управления данными ПЕРСОНАЖЕЙ в Redis.
    Оперирует Hash-объектами персонажей и глобальной статистикой мира.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ CharacterCacheManager (v2) инициализирован.")

    # --- Методы для управления данными персонажей ---

    # 🔥 ИЗМЕНЕНИЕ: Метод теперь принимает account_id для построения ключа
    async def get_character_snapshot(self, account_id: str, character_id: str) -> Optional[Dict[str, Any]]:
        """Получает полный слепок данных персонажа из его Hash-объекта."""
        key = KEY_CHARACTER_DATA.format(account_id=account_id, character_id=character_id)
        # Получаем значение поля 'snapshot' из Hash'а
        snapshot_str = await self.redis.hget(key, FIELD_CHARACTER_SNAPSHOT)
        if snapshot_str:
            logger.debug(f"Получен снапшот персонажа {character_id} (аккаунт {account_id}) из Redis.")
            return json.loads(snapshot_str)
        
        logger.debug(f"Снапшот персонажа {character_id} (аккаунт {account_id}) не найден в Redis.")
        return None

    # 🔥 ИЗМЕНЕНИЕ: Метод теперь принимает account_id и работает с HSET
    async def set_character_snapshot(self, account_id: str, character_id: str, snapshot_data: Dict[str, Any], is_online: bool = True):
        """Сохраняет полный слепок данных персонажа в поле 'snapshot' его Hash-объекта."""
        key = KEY_CHARACTER_DATA.format(account_id=account_id, character_id=character_id)
        value = json.dumps(snapshot_data)
        await self.redis.hset(key, FIELD_CHARACTER_SNAPSHOT, value)

        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None:
            await self.redis.expire(key, ttl)
        logger.debug(f"Снапшот персонажа {character_id} сохранен/обновлен в Redis с TTL={ttl}.")

    # 🔥 ИЗМЕНЕНИЕ: Метод теперь принимает account_id
    async def delete_character_snapshot(self, account_id: str, character_id: str):
        """Удаляет весь Hash-объект персонажа."""
        key = KEY_CHARACTER_DATA.format(account_id=account_id, character_id=character_id)
        await self.redis.delete(key)
        logger.info(f"Данные персонажа {character_id} (весь Hash) удалены из Redis.")

    # 🔥 ИЗМЕНЕНИЕ: Метод теперь принимает account_id
    async def update_character_snapshot_ttl(self, account_id: str, character_id: str, is_online: bool = True):
        """Обновляет TTL для всего Hash-объекта персонажа."""
        key = KEY_CHARACTER_DATA.format(account_id=account_id, character_id=character_id)
        ttl = DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE if is_online else DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE
        if ttl is not None and await self.redis.exists(key):
            await self.redis.expire(key, ttl)
            logger.debug(f"TTL для персонажа {character_id} обновлен до {ttl}.")

    # --- 🔥 ИЗМЕНЕНИЕ: Все методы для привязки аккаунтов УДАЛЕНЫ ---
    # Логика get_character_id_by_discord_id, set_character_id_for_discord_id
    # и delete_character_id_for_discord_id должна быть перенесена
    # в отдельный AccountCacheManager.

    # --- Методы для управления глобальной статистикой ---

    # 🔥 ИЗМЕНЕНИЕ: Работаем с полем в Hash'е статистики через HINCRBY
    async def decrement_pool_count(self) -> int:
        """Уменьшает на 1 счетчик доступных персонажей в пуле."""
        new_count = await self.redis.hincrby(KEY_WORLD_STATS, FIELD_CHARACTER_POOL_AVAILABLE, -1)
        logger.info(f"Счетчик персонажей в пуле уменьшен. Новое значение: {new_count}")
        return new_count

    # 🔥 ИЗМЕНЕНИЕ: Работаем с полем в Hash'е статистики через HGET
    async def get_pool_count(self) -> int:
        """Получает текущее значение счетчика доступных персонажей."""
        count = await self.redis.hget(KEY_WORLD_STATS, FIELD_CHARACTER_POOL_AVAILABLE)
        return int(count) if count else 0