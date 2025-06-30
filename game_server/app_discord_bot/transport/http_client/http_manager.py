# transport/http_client/http_manager.py
import aiohttp
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.http_client.interfaces.i_auth_api import IAuthAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_discord_api import IDiscordAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_gateway_api import IGatewayAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_shard_api import IShardAPIRoutes
from game_server.app_discord_bot.transport.http_client.interfaces.i_state_entity_api import IStateEntityAPIRoutes

# --- Импортируем ИНТЕРФЕЙСЫ для типизации ---


# --- Импортируем РЕАЛИЗАЦИИ для инстанцирования ---
from .routes.auth_api_impl import AuthAPIRoutesImpl
from .routes.discord_api_impl import DiscordAPIRoutesImpl
from .routes.gateway_api_impl import GatewayAPIRoutesImpl
from .routes.shard_api_impl import ShardAPIRoutesImpl
from .routes.state_entity_api_impl import StateEntityAPIRoutesImpl

class HTTPManager:
    """Центральный менеджер, который агрегирует все API-менеджеры."""
    # Типизируем свойства через ИНТЕРФЕЙСЫ
    auth: IAuthAPIRoutes
    discord: IDiscordAPIRoutes
    gateway: IGatewayAPIRoutes
    shard: IShardAPIRoutes
    state_entity: IStateEntityAPIRoutes

    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        if not base_url:
            raise ValueError("Base API URL is not set.")

        # Инициализируем свойства через РЕАЛИЗАЦИИ
        self.auth = AuthAPIRoutesImpl(session=session, base_url=base_url)
        self.discord = DiscordAPIRoutesImpl(session=session, base_url=base_url)
        self.gateway = GatewayAPIRoutesImpl(session=session, base_url=base_url)
        self.shard = ShardAPIRoutesImpl(session=session, base_url=base_url)
        self.state_entity = StateEntityAPIRoutesImpl(session=session, base_url=base_url)
        
        logger.info("Все доменные API-менеджеры инициализированы.")

# Фабричная функция для создания экземпляра
async def create_http_manager(base_url: str) -> HTTPManager:
    """Создает aiohttp.ClientSession и инициализирует HTTPManager."""
    session = aiohttp.ClientSession(
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    manager = HTTPManager(session=session, base_url=base_url)
    # Сохраняем сессию для корректного закрытия
    setattr(manager, '_session_to_close', session)
    return manager
