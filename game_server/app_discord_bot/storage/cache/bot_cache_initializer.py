# game_server/app_discord_bot/storage/cache/bot_cache_initializer.py

# 🔥 ИЗМЕНЕНИЕ: Удаляем ненужные импорты, которые использовались только BotCacheInitializer
# from typing import Any, Dict


from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.managers.pending_request_manager import PendingRequestManager
from game_server.app_discord_bot.storage.cache.managers.player_session_manager import PlayerSessionManager
# ▼▼▼ НОВЫЙ ИМПОРТ: Менеджер данных игрового мира ▼▼▼
from game_server.app_discord_bot.storage.cache.managers.game_world_data_manager import GameWorldDataManager
import inject 
import logging 


class BotCache:
    pending_requests: PendingRequestManager
    guild_config: GuildConfigManager
    player_sessions: PlayerSessionManager
    account_data: AccountDataManager
    # ▼▼▼ НОВЫЙ АТРИБУТ: Менеджер данных игрового мира ▼▼▼
    game_world_data: GameWorldDataManager

    # 🔥 ИЗМЕНЕНИЕ: Конструктор теперь использует inject.autoparams() БЕЗ СТРОКОВЫХ КЛЮЧЕЙ
    @inject.autoparams() 
    def __init__(
        self,
        # Имена параметров должны совпадать с атрибутами, но DI будет разрешать по типам
        pending_request_manager: PendingRequestManager, # ИЗМЕНЕНО: pending_request_manager (без "s")
        guild_config_manager: GuildConfigManager,
        player_session_manager: PlayerSessionManager,
        account_data_manager: AccountDataManager,
        # ▼▼▼ НОВЫЙ ПАРАМЕТР КОНСТРУКТОРА: Менеджер данных игрового мира ▼▼▼
        game_world_data_manager: GameWorldDataManager,
        
        logger: logging.Logger 
    ):
        self.pending_requests = pending_request_manager # ИЗМЕНЕНО: pending_request_manager
        self.guild_config = guild_config_manager
        self.player_sessions = player_session_manager
        self.account_data = account_data_manager
        # ▼▼▼ ПРИСВАИВАНИЕ НОВОГО МЕНЕДЖЕРА ▼▼▼
        self.game_world_data = game_world_data_manager
        self.logger = logger
        self.logger.info("✅ BotCache (DI-ready) инициализирован.")
        print("DEBUG_PRINT_BC: ✨ BotCache инициализирован.") # Оставил для отладки
        # ▼▼▼ ДОБАВЛЕННЫЙ PRINT ДЛЯ ОТЛАДКИ ▼▼▼
        print("DEBUG_PRINT_BC: GameWorldDataManager добавлен в BotCache.")
