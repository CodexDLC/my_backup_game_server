# game_server/app_discord_bot/core/di_modules/bot_service_bindings.py

from typing import Any
import inject
from discord.ext import commands

# Импортируем все ваши сервисы
from game_server.app_discord_bot.app.events.player_events_handler import PlayerEventsHandler
from game_server.app_discord_bot.app.services.admin.article_management_service import ArticleManagementService
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.app.services.admin.discord_entity_service import DiscordEntityService
from game_server.app_discord_bot.app.services.admin.hub_layout_service import HubLayoutService
from game_server.app_discord_bot.app.services.admin.role_management_service import RoleManagementService
from game_server.app_discord_bot.app.services.authentication.authentication_service import AuthenticationService
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager
from game_server.app_discord_bot.app.services.utils.navigation_helper import NavigationHelper
from game_server.app_discord_bot.app.services.world_location.game_world_data_loader_service import GameWorldDataLoaderService
from game_server.app_discord_bot.app.services.utils.message_sender_service import MessageSenderService
from game_server.app_discord_bot.app.services.utils.player_login_intent_processor import PlayerLoginIntentProcessor
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.app.services.utils.role_verification_service import RoleVerificationService
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG

def configure_bot_services(binder, bot_instance: Any):
    """
    Конфигурирует все сервисы бота.
    """
    binder.bind_to_constructor(RoleManagementService, RoleManagementService)
    binder.bind_to_constructor(DiscordEntityService, DiscordEntityService)
    binder.bind_to_constructor(BaseDiscordOperations, BaseDiscordOperations)
    binder.bind_to_constructor(CacheSyncManager, CacheSyncManager)
    binder.bind_to_constructor(ArticleManagementService, ArticleManagementService)
    binder.bind_to_constructor(HubLayoutService, HubLayoutService)
    binder.bind_to_constructor(RequestHelper, RequestHelper)
    binder.bind_to_constructor(RoleVerificationService, RoleVerificationService)
    binder.bind_to_constructor(PlayerEventsHandler, PlayerEventsHandler)
    binder.bind_to_constructor(PlayerLoginIntentProcessor, PlayerLoginIntentProcessor)
    binder.bind_to_constructor(MessageSenderService, MessageSenderService)
    binder.bind_to_constructor(AuthenticationService, AuthenticationService)
    binder.bind_to_constructor(RoleFinder, RoleFinder)
    binder.bind_to_constructor(GameWorldDataLoaderService, GameWorldDataLoaderService)
    binder.bind_to_constructor(InteractionResponseManager, InteractionResponseManager)
    binder.bind_to_constructor(NavigationHelper, NavigationHelper)
    
    # Привязка простых значений остается без изменений
    binder.bind('emojis_formatting_config', CHANNELS_CONFIG["emojis_formatting"])
