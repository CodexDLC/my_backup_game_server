# game_server/app_discord_bot/transport/http_client/interfaces/i_auth_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

from game_server.contracts.api_models.system.requests import DiscordShardLoginRequest, HubRoutingRequest # Добавлен Tuple для возвращаемого типа


# Импортируем Pydantic модели, которые используются в методах


class IAuthAPIRoutes(ABC):
    """
    Абстрактный интерфейс (контракт) для методов API аутентификации.
    """

    @abstractmethod
    async def hub_login(self, data: HubRoutingRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]: # ИСПРАВЛЕНО: Добавлен headers и возвращаемый тип
        """Инициировать регистрацию/первичный вход через Хаб.""" # Обновлен Docstring
        raise NotImplementedError

    @abstractmethod
    async def session_login(self, data: DiscordShardLoginRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]: # ИСПРАВЛЕНО: Добавлен headers и возвращаемый тип
        """Инициировать создание игровой сессии."""
        raise NotImplementedError