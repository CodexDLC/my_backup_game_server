from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from game_server.database.models.models import EliteMonster # Предполагается, что такая модель существует

class IEliteMonsterRepository(ABC):
    @abstractmethod
    async def get_monster_by_id(self, monster_id: int) -> Optional[EliteMonster]: pass
    @abstractmethod
    async def get_monster_by_name(self, name: str) -> Optional[EliteMonster]: pass
    @abstractmethod
    async def get_all_monsters(self) -> List[EliteMonster]: pass
    @abstractmethod
    async def create_monster(self, data: Dict[str, Any]) -> EliteMonster: pass
    @abstractmethod
    async def update_monster(self, monster_id: int, updates: Dict[str, Any]) -> Optional[EliteMonster]: pass
    @abstractmethod
    async def delete_monster(self, monster_id: int) -> bool: pass