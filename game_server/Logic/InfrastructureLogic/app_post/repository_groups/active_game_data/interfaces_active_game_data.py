from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from game_server.database.models.models import InstancedItem, UsedCharacterArchive

class IItemInstanceRepository(ABC):
    @abstractmethod
    async def create_item_instance(self, data: Dict[str, Any]) -> InstancedItem: pass
    @abstractmethod
    async def get_item_instance_by_id(self, instance_id: int) -> Optional[InstancedItem]: pass
    @abstractmethod
    async def get_items_by_owner(self, owner_id: int, owner_type: str, location_type: Optional[str] = None) -> List[InstancedItem]: pass
    @abstractmethod
    async def update_item_instance(self, instance_id: int, updates: Dict[str, Any]) -> Optional[InstancedItem]: pass
    @abstractmethod
    async def delete_item_instance(self, instance_id: int) -> bool: pass
    @abstractmethod
    async def transfer_item_instance(self, instance_id: int, new_owner_id: int, new_owner_type: str, new_location_type: str, new_location_slot: Optional[str] = None) -> Optional[InstancedItem]: pass

class IUsedCharacterArchiveRepository(ABC):
    @abstractmethod
    async def create_entry(self, original_pool_id: int, linked_entity_id: int, activation_type: str, linked_account_id: Optional[int] = None, simplified_pool_data: Optional[Dict[str, Any]] = None) -> UsedCharacterArchive: pass
    @abstractmethod
    async def get_entry_by_id(self, archive_id: int) -> Optional[UsedCharacterArchive]: pass
    @abstractmethod
    async def update_status(self, archive_id: int, new_status: str) -> Optional[UsedCharacterArchive]: pass
    @abstractmethod
    async def delete_entry(self, archive_id: int) -> bool: pass