# transport/http_client/routes/interfaces/i_shard_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO








class IShardAPIRoutes(ABC):
    """Абстрактный интерфейс для методов API управления шардами."""

    @abstractmethod
    async def register(self, data: SaveShardCommandDTO) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
