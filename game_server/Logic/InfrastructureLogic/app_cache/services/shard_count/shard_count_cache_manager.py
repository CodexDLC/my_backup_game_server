# game_server/Logic/InfrastructureLogic/app_cache/services/shard_count/shard_count_cache_manager.py

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod # Добавлено

# Импорт CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_shard_count_cache import IShardCountCacheManager
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Изменено

# Импорт нового интерфейса


# Константа для ключа Redis
# Можно вынести в game_server/config/constants/redis.py, если это уже используется
REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX = "shard:players_count"

# Изменяем класс ShardCountCacheManager, чтобы он наследовал от IShardCountCacheManager
class ShardCountCacheManager(IShardCountCacheManager): # Изменено
    """
    Менеджер для работы со счетчиками игроков на шарадах в Redis.
    Предоставляет методы для атомарного инкремента/декремента и установки значений.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ ShardCountCacheManager инициализирован.") # Изменено: используем logger

    async def get_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Получает текущее количество игроков для заданного шарда из Redis.
        """
        key = f"{REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX}:{discord_guild_id}"
        count = await self.redis.get(key)
        if count:
            logger.debug(f"Получен счетчик игроков для шарда {discord_guild_id} из Redis: {count}")
            return int(count)
        logger.debug(f"Счетчик игроков для шарда {discord_guild_id} не найден в Redis, возвращено 0.")
        return 0

    async def increment_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Атомарно инкрементирует счетчик игроков для заданного шарда в Redis.
        Возвращает новое значение счетчика.
        """
        key = f"{REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX}:{discord_guild_id}"
        new_count = await self.redis.incr(key)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} инкрементирован до: {new_count}")
        return new_count

    async def decrement_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Атомарно декрементирует счетчик игроков для заданного шарда в Redis.
        Возвращает новое значение счетчика. Счетчик не может быть отрицательным.
        """
        key = f"{REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX}:{discord_guild_id}"
        # Проверяем, чтобы счетчик не ушел в минус, если это необходимо
        current_count = await self.get_shard_player_count(discord_guild_id)
        if current_count <= 0:
            logger.warning(f"Попытка декрементировать счетчик шарда {discord_guild_id}, но он уже <= 0. Возвращено 0.")
            return 0

        new_count = await self.redis.decr(key)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} декрементирован до: {new_count}")
        return new_count

    async def set_shard_player_count(self, discord_guild_id: int, count: int):
        """
        Устанавливает счетчик игроков для заданного шарда в Redis до определенного значения.
        Используется для инициализации или синхронизации.
        """
        key = f"{REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX}:{discord_guild_id}"
        await self.redis.set(key, count)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} установлен в Redis на: {count}")

    async def delete_shard_player_count(self, discord_guild_id: int):
        """
        Удаляет счетчик игроков для заданного шарда из Redis.
        Может быть полезно при удалении шарда.
        """
        key = f"{REDIS_KEY_SHARD_PLAYER_COUNT_PREFIX}:{discord_guild_id}"
        await self.redis.delete(key)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} удален из Redis.")