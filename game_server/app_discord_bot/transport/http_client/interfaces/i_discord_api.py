# transport/http_client/routes/interfaces/i_discord_api.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple



from game_server.common_contracts.api_models.discord_api import GetDiscordEntitiesRequest, GuildConfigSyncRequest, UnifiedEntityBatchDeleteRequest, UnifiedEntitySyncRequest



class IDiscordAPIRoutes(ABC):
    """Абстрактный интерфейс для методов API работы с Discord сущностями."""

    @abstractmethod
    async def sync_entities(self, data: UnifiedEntitySyncRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_entities(self, data: GetDiscordEntitiesRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def batch_delete_entities(self, data: UnifiedEntityBatchDeleteRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def sync_config_from_bot(self, data: GuildConfigSyncRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        raise NotImplementedError