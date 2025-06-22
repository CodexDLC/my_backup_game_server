from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from game_server.database.models.models import AutoSession, XpTickData

class IAutoSessionRepository(ABC):
    @abstractmethod
    async def create_session(self, character_id: int, active_category: str, interval_minutes: int = 6) -> AutoSession: pass
    @abstractmethod
    async def get_session(self, character_id: int) -> Optional[AutoSession]: pass
    @abstractmethod
    async def update_session(self, character_id: int, update_data: Dict[str, Any]) -> Optional[AutoSession]: pass
    @abstractmethod
    async def delete_session(self, character_id: int) -> bool: pass
    @abstractmethod
    async def get_ready_sessions(self) -> List[AutoSession]: pass
    @abstractmethod
    async def update_character_tick_time(self, character_id: int, interval_minutes: int = 6) -> Optional[AutoSession]: pass

class IXpTickDataRepository(ABC):
    @abstractmethod
    async def bulk_create_xp_data(self, xp_data_list: List[Dict[str, Any]]) -> int: pass
    @abstractmethod
    async def get_all_xp_data_for_character(self, character_id: int) -> List[XpTickData]: pass
    @abstractmethod
    async def delete_all_xp_data_for_character(self, character_id: int) -> bool: pass