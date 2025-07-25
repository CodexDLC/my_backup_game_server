# game_server/app_discord_bot/core/di_modules/bot_transport_bindings.py

from typing import Any
import inject
import logging
import aiohttp

from game_server.app_discord_bot.config.discord_settings import BOT_NAME_FOR_GATEWAY

from game_server.app_discord_bot.transport.http_client.interfaces.i_auth_api import IAuthAPIRoutes
from game_server.app_discord_bot.transport.http_client.routes.auth_api_impl import AuthAPIRoutesImpl

from game_server.app_discord_bot.transport.websocket_client.handlers.event_handlers import WSEventHandlers

from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager as TransportPendingRequestsManager


from discord.ext import commands

from game_server.config.settings_core import GAME_SERVER_API

def configure_bot_transport(binder, bot_instance: Any):
    """
    Конфигурирует связывания для транспортного слоя Discord-бота.
    """
    binder.bind_to_constructor(WebSocketManager, WebSocketManager)
    # Используем псевдоним, чтобы избежать конфликта имен, если он есть
    binder.bind_to_constructor(TransportPendingRequestsManager, TransportPendingRequestsManager)
    
    binder.bind_to_constructor(WSEventHandlers, WSEventHandlers)


    # 🔥 НОВАЯ ПРИВЯЗКА: Привязываем интерфейс IAuthAPIRoutes к его реализации AuthAPIRoutesImpl
    # Передаем необходимые зависимости в конструктор AuthAPIRoutesImpl
    binder.bind_to_provider(IAuthAPIRoutes, lambda: AuthAPIRoutesImpl(
        session=inject.instance(aiohttp.ClientSession), # aiohttp.ClientSession должен быть привязан где-то еще (например, в di_container.py)
        base_url=GAME_SERVER_API, # Из discord_settings
        client_id=BOT_NAME_FOR_GATEWAY # Из discord_settings
    ))