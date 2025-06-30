# game_server/Logic/InfrastructureLogic/app_cache/services/shard_count/shard_count_cache_manager.py
import logging
from typing import Optional

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_shard_count_cache import IShardCountCacheManager
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 ИЗМЕНЕНИЕ: Импортируем константы из нового файла
from game_server.config.constants.redis_key.shard_keys import KEY_SHARD_STATS, FIELD_SHARD_PLAYER_COUNT


class ShardCountCacheManager(IShardCountCacheManager):
    """
    Менеджер для работы со счетчиками игроков на шарадах в Redis.
    Использует Hash для хранения статистики по каждому шарду.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ ShardCountCacheManager (v2) инициализирован.")

    async def get_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Получает текущее количество игроков для заданного шарда из поля в Hash.
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон ключа
        key = KEY_SHARD_STATS.format(discord_guild_id=discord_guild_id)
        # 🔥 ИЗМЕНЕНИЕ: Получаем значение поля из Hash
        count = await self.redis.hget(key, FIELD_SHARD_PLAYER_COUNT)
        if count:
            logger.debug(f"Получен счетчик игроков для шарда {discord_guild_id} из Redis: {count}")
            return int(count)
        logger.debug(f"Счетчик игроков для шарда {discord_guild_id} не найден в Redis, возвращено 0.")
        return 0

    async def increment_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Атомарно инкрементирует счетчик игроков для заданного шарда в поле Hash.
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон ключа
        key = KEY_SHARD_STATS.format(discord_guild_id=discord_guild_id)
        # 🔥 ИЗМЕНЕНИЕ: Инкрементируем значение поля в Hash
        new_count = await self.redis.hincrby(key, FIELD_SHARD_PLAYER_COUNT, 1)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} инкрементирован до: {new_count}")
        return new_count

    async def decrement_shard_player_count(self, discord_guild_id: int) -> int:
        """
        Атомарно декрементирует счетчик игроков для заданного шарда в поле Hash.
        """
        key = KEY_SHARD_STATS.format(discord_guild_id=discord_guild_id)
        
        # Проверка остается полезной, но теперь она внутри Hash
        current_count = await self.get_shard_player_count(discord_guild_id)
        if current_count <= 0:
            logger.warning(f"Попытка декрементировать счетчик шарда {discord_guild_id}, но он уже <= 0. Возвращено 0.")
            return 0
        
        # 🔥 ИЗМЕНЕНИЕ: Декрементируем значение поля в Hash
        new_count = await self.redis.hincrby(key, FIELD_SHARD_PLAYER_COUNT, -1)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} декрементирован до: {new_count}")
        return new_count

    async def set_shard_player_count(self, discord_guild_id: int, count: int):
        """
        Устанавливает счетчик игроков для заданного шарда в поле Hash.
        """
        key = KEY_SHARD_STATS.format(discord_guild_id=discord_guild_id)
        # 🔥 ИЗМЕНЕНИЕ: Устанавливаем значение поля в Hash
        await self.redis.hset(key, FIELD_SHARD_PLAYER_COUNT, count)
        logger.info(f"Счетчик игроков для шарда {discord_guild_id} установлен в Redis на: {count}")

    async def delete_shard_player_count(self, discord_guild_id: int):
        """

        Удаляет только поле счетчика игроков, не трогая весь Hash статистики.
        """
        key = KEY_SHARD_STATS.format(discord_guild_id=discord_guild_id)
        # 🔥 ИЗМЕНЕНИЕ: Удаляем только поле из Hash
        await self.redis.hdel(key, FIELD_SHARD_PLAYER_COUNT)
        logger.info(f"Поле счетчика игроков для шарда {discord_guild_id} удалено из Hash статистики.")