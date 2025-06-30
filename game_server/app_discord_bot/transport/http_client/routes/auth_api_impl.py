# transport/http_client/routes/auth_api_impl.py
import aiohttp
from typing import Optional, Dict, Any


from game_server.common_contracts.api_models.auth_api import DiscordShardLoginRequest, HubRoutingRequest
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.http_client.interfaces.i_auth_api import IAuthAPIRoutes


# Импортируем интерфейс, который мы реализуем



class AuthAPIRoutesImpl(IAuthAPIRoutes):
    """
    Конкретная реализация методов для взаимодействия с эндпоинтами аутентификации.
    """
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = f"{base_url}/auth"

    async def hub_login(self, data: HubRoutingRequest) -> Optional[Dict[str, Any]]:
        """Инициировать вход через Хаб."""
        try:
            async with self._session.post(f"{self._base_url}/hub_login", json=data.model_dump()) as response:
                if response.status == 202:
                    return await response.json()
                logger.warning(f"Ошибка hub_login. Статус: {response.status}, Ответ: {await response.text()}")
                return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента при hub_login: {e}", exc_info=True)
            return None

    async def session_login(self, data: DiscordShardLoginRequest) -> Optional[Dict[str, Any]]:
        """Инициировать создание игровой сессии."""
        try:
            async with self._session.post(f"{self._base_url}/session_login", json=data.model_dump()) as response:
                if response.status == 202:
                    return await response.json()
                logger.warning(f"Ошибка session_login. Статус: {response.status}, Ответ: {await response.text()}")
                return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента при session_login: {e}", exc_info=True)
            return None
