from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union, Tuple
from game_server.database.models.models import (
    CharacterPool, EquipmentTemplate # StaticItemTemplate УДАЛЕНО
)
from sqlalchemy.ext.asyncio import AsyncSession

UnifiedIdType = Union[int, str]


class ICharacterPoolRepository(ABC):
    @abstractmethod
    async def create(self, character_data: Dict[str, Any]) -> CharacterPool: pass
    @abstractmethod
    async def upsert(self, character_data: Dict[str, Any]) -> CharacterPool: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[CharacterPool]: pass
    @abstractmethod
    async def get_many(self, offset: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[CharacterPool]: pass
    @abstractmethod
    async def update(self, id: int, update_data: Dict[str, Any]) -> Optional[CharacterPool]: pass
    @abstractmethod
    async def delete(self, id: int) -> bool: pass
    @abstractmethod
    async def get_all(self) -> List[CharacterPool]: pass
    @abstractmethod
    async def find_one_available_and_lock(self) -> Optional[CharacterPool]: pass
    @abstractmethod
    async def delete_character(self, character: CharacterPool) -> bool: pass



class IEquipmentTemplateRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> EquipmentTemplate: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[EquipmentTemplate]: pass
    @abstractmethod
    async def get_by_item_code(self, item_code: str) -> Optional[EquipmentTemplate]: pass
    @abstractmethod
    async def get_all_item_codes(self) -> List[str]: pass
    @abstractmethod
    async def get_all(self) -> List[EquipmentTemplate]: pass
    @abstractmethod
    async def update(self, item_code: str, updates: Dict[str, Any]) -> Optional[EquipmentTemplate]: pass
    @abstractmethod
    async def delete(self, id: int) -> bool: pass
    @abstractmethod
    async def delete_by_item_code(self, item_code: str) -> bool: pass
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> EquipmentTemplate: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass

# УДАЛЕНО: IStaticItemTemplateRepository