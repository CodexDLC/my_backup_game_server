# game_server/app_discord_bot/transport/http_client/http_manager.py
import aiohttp
from game_server.app_discord_bot.transport.http_client.interfaces.i_discord_api import IDiscordAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_gateway_api import IGatewayAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_shard_api import IShardAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_state_entity_api import IStateEntityAPIRoutes
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.http_client.routes.auth_api_impl import AuthAPIRoutesImpl
from game_server.app_discord_bot.transport.http_client.routes.discord_api_impl import DiscordAPIRoutesImpl
from game_server.app_discord_bot.transport.http_client.routes.gateway_api_impl import GatewayAPIRoutesImpl
from game_server.app_discord_bot.transport.http_client.routes.shard_api_impl import ShardAPIRoutesImpl
from game_server.app_discord_bot.transport.http_client.routes.state_entity_api_impl import StateEntityAPIRoutesImpl

# 🔥 НОВОЕ: Импортируем сам модуль discord_settings, чтобы получать константы напрямую
from game_server.app_discord_bot.config import discord_settings


class HTTPManager:
    auth: AuthAPIRoutesImpl
    discord: IDiscordAPIRoutes
    gateway: IGatewayAPIRoutes
    shard: IShardAPIRoutes
    state_entity: IStateEntityAPIRoutes

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем конкретные URL и имя бота как аргументы
    def __init__(self, session: aiohttp.ClientSession, base_http_api_url: str, bot_name_for_gateway: str):
        self._session = session
        self._base_http_api_url = base_http_api_url
        self._bot_name_for_gateway = bot_name_for_gateway

        # Инициализируем свойства через РЕАЛИЗАЦИИ, используя переданные аргументы
        self.auth = AuthAPIRoutesImpl(session, self._base_http_api_url, self._bot_name_for_gateway)
        self.discord = DiscordAPIRoutesImpl(session, self._base_http_api_url)
        self.gateway = GatewayAPIRoutesImpl(session, self._base_http_api_url)
        self.shard = ShardAPIRoutesImpl(session, self._base_http_api_url)
        self.state_entity = StateEntityAPIRoutesImpl(session, self._base_http_api_url)
        
        logger.info("Все доменные API-менеджеры инициализированы.")

# Фабричная функция для создания экземпляра
# 🔥 ИЗМЕНЕНИЕ: Принимаем нужные константы напрямую
async def create_http_manager(session: aiohttp.ClientSession, base_http_api_url: str, bot_name_for_gateway: str) -> HTTPManager:
    manager = HTTPManager(session=session, base_http_api_url=base_http_api_url, bot_name_for_gateway=bot_name_for_gateway)
    setattr(manager, '_session_to_close', session)
    return manager