# Discord_API/core/app_cache_discord/interfaces/pending_request_manager_interface.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IPendingRequestManager(ABC):
    """Интерфейс для менеджера ожидающих запросов."""

    @abstractmethod
    async def store_request(self, command_id: str, interaction_data: Dict[str, Any], ttl: int):
        pass

    @abstractmethod
    async def retrieve_and_delete_request(self, command_id: str) -> Optional[Dict[str, Any]]:
        pass