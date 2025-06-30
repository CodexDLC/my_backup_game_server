# Discord_API/core/app_cache_discord/bot_cache_initializer.py
from typing import Any, Dict

from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.managers.pending_request_manager import PendingRequestManager
# 🔥 ИЗМЕНЕНИЕ: Импортируем правильный класс из правильного файла
from game_server.app_discord_bot.storage.cache.managers.player_session_manager import PlayerSessionManager


class BotCache:
    """
    Класс-контейнер для всех менеджеров кэша бота.
    """
    pending_requests: PendingRequestManager
    guild_config: GuildConfigManager
    # 🔥 ИЗМЕНЕНИЕ: Атрибут переименован для ясности и использует новый тип
    player_sessions: PlayerSessionManager

    def __init__(self, pending_requests: PendingRequestManager, guild_config: GuildConfigManager, player_sessions: PlayerSessionManager):
        self.pending_requests = pending_requests
        self.guild_config = guild_config
        # 🔥 ИЗМЕНЕНИЕ: Присваиваем переименованный атрибут
        self.player_sessions = player_sessions


class BotCacheInitializer:
    """
    Инициализатор для всех менеджеров кэша бота.
    """
    def initialize(self, redis_client: DiscordRedisClient) -> BotCache:
        """
        Инициализирует и возвращает контейнер с менеджерами кэша.
        """
        pending_requests_manager = PendingRequestManager(redis_client)
        guild_config_manager = GuildConfigManager(redis_client)
        # 🔥 ИЗМЕНЕНИЕ: Создаем экземпляр нового менеджера сессий
        player_session_manager = PlayerSessionManager(redis_client)

        return BotCache(
            pending_requests=pending_requests_manager,
            guild_config=guild_config_manager,
            # 🔥 ИЗМЕНЕНИЕ: Передаем новый менеджер в конструктор
            player_sessions=player_session_manager
        )