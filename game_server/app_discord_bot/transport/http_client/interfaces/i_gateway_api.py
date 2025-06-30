# transport/http_client/routes/interfaces/i_gateway_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from game_server.common_contracts.api_models.gateway_api import BotAcknowledgementRequest






class IGatewayAPIRoutes(ABC):
    """Абстрактный интерфейс для методов API шлюза."""

    @abstractmethod
    async def acknowledge_command(self, command_id: str, data: BotAcknowledgementRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
