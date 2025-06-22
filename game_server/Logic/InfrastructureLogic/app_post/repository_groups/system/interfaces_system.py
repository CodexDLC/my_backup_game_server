from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from game_server.database.models.models import DataVersion # Предполагается, что такая модель существует

class IDataVersionRepository(ABC):
    @abstractmethod
    async def get_current_version(self) -> Optional[DataVersion]: pass
    @abstractmethod
    async def update_version(self, new_version: str) -> Optional[DataVersion]: pass
    @abstractmethod
    async def create_initial_version(self, version_data: Dict[str, Any]) -> DataVersion: pass