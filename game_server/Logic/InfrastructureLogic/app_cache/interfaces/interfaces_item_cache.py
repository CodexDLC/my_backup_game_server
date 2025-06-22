# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_item_cache.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IItemCacheManager(ABC):
    @abstractmethod
    async def get_item_instance_data(self, item_uuid: str) -> Optional[Dict[str, Any]]: pass

    @abstractmethod
    async def set_item_instance_data(self, item_uuid: str, item_data: Dict[str, Any], ttl_seconds: Optional[int] = None): pass

    @abstractmethod
    async def delete_item_instance_data(self, item_uuid: str): pass

    @abstractmethod
    async def get_multiple_item_instances_data(self, item_uuids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]: pass