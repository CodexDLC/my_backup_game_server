# game_server/app_discord_bot/core/di_modules/bot_cache_bindings.py

import inject
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager
from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager
from game_server.app_discord_bot.storage.cache.interfaces.player_session_manager_interface import IPlayerSessionManager
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.storage.cache.managers.character_cache_manager import CharacterCacheManagerImpl
from game_server.app_discord_bot.storage.cache.managers.game_world_data_manager import GameWorldDataManager
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.managers.player_session_manager import PlayerSessionManager
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache

from game_server.app_discord_bot.storage.cache.interfaces.pending_request_manager_interface import IPendingRequestManager
from game_server.app_discord_bot.storage.cache.managers.pending_request_manager import PendingRequestManager

def configure_bot_cache(binder):
    binder.bind_to_constructor(IPendingRequestManager, PendingRequestManager)
    binder.bind_to_constructor(IGuildConfigManager, GuildConfigManager)
    binder.bind_to_constructor(IPlayerSessionManager, PlayerSessionManager)    
    binder.bind_to_constructor(IAccountDataManager, AccountDataManager)
    binder.bind_to_constructor(IGameWorldDataManager, GameWorldDataManager)
    binder.bind_to_constructor(ICharacterCacheManager, CharacterCacheManagerImpl)
    
    binder.bind_to_constructor(BotCache, BotCache)
    