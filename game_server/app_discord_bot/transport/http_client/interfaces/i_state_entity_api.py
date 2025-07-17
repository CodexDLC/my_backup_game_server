# transport/http_client/routes/interfaces/i_state_entity_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from game_server.contracts.api_models.system.requests import GetStateEntityByKeyRequest
from game_server.contracts.shared_models.base_requests import BaseRequest






class IStateEntityAPIRoutes(ABC):
    """Абстрактный интерфейс для методов API сущностей состояния."""

    @abstractmethod
    async def get_all(self, data: BaseRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_key(self, data: GetStateEntityByKeyRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
