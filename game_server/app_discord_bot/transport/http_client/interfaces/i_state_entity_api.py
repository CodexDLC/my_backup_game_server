# transport/http_client/routes/interfaces/i_state_entity_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from game_server.common_contracts.api_models.system_api import GetStateEntityByKeyRequest
from game_server.common_contracts.shared_models.api_contracts import BaseRequest





class IStateEntityAPIRoutes(ABC):
    """Абстрактный интерфейс для методов API сущностей состояния."""

    @abstractmethod
    async def get_all(self, data: BaseRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_key(self, data: GetStateEntityByKeyRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
