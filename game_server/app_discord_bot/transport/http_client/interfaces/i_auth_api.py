# transport/http_client/routes/interfaces/i_auth_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from game_server.common_contracts.api_models.auth_api import DiscordShardLoginRequest, HubRoutingRequest




# Импортируем Pydantic модели, которые используются в методах


class IAuthAPIRoutes(ABC):
    """
    Абстрактный интерфейс (контракт) для методов API аутентификации.
    """

    @abstractmethod
    async def hub_login(self, data: HubRoutingRequest) -> Optional[Dict[str, Any]]:
        """Инициировать вход через Хаб."""
        raise NotImplementedError

    @abstractmethod
    async def session_login(self, data: DiscordShardLoginRequest) -> Optional[Dict[str, Any]]:
        """Инициировать создание игровой сессии."""
        raise NotImplementedError
