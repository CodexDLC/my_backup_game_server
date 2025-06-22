from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import uuid
from game_server.database.models.models import StateEntity, GameLocation

class IStateEntityRepository(ABC):
    @abstractmethod
    async def create(self, entity_data: Dict[str, Any]) -> StateEntity: pass # ИЗМЕНЕНО
    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[StateEntity]: pass # ИЗМЕНЕНО
    @abstractmethod
    async def get_by_access_code(self, access_code: str) -> Optional[StateEntity]: pass # НОВЫЙ МЕТОД
    @abstractmethod
    async def get_all(self) -> List[StateEntity]: pass # ИЗМЕНЕНО
    @abstractmethod
    async def update(self, access_code: str, updates: Dict[str, Any]) -> Optional[StateEntity]: pass # ИЗМЕНЕНО
    @abstractmethod
    async def delete(self, access_code: str) -> bool: pass # ИЗМЕНЕНО
    @abstractmethod
    async def upsert(self, entity_data: Dict[str, Any]) -> StateEntity: pass # НОВЫЙ МЕТОД

class IGameLocationRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> GameLocation:
        """Создает новую запись локации мира."""
        pass

    @abstractmethod
    async def get_by_id(self, location_id: uuid.UUID) -> Optional[GameLocation]:
        """Получает локацию по её UUID ID."""
        pass

    @abstractmethod
    async def get_by_access_key(self, access_key: str) -> Optional[GameLocation]:
        """Получает локацию по её access_key."""
        pass

    @abstractmethod
    async def get_all(self) -> List[GameLocation]:
        """Получает все локации из базы данных."""
        pass

    @abstractmethod
    async def get_locations_by_skeleton_template(self, skeleton_template_id: str) -> List[GameLocation]:
        """Получает все локации, принадлежащие определенному шаблону скелета мира."""
        pass

    @abstractmethod
    async def get_children_locations(self, parent_access_key: str) -> List[GameLocation]:
        """Получает все дочерние локации для заданного родительского access_key."""
        pass

    @abstractmethod
    async def update(self, access_key: str, updates: Dict[str, Any]) -> Optional[GameLocation]:
        """Обновляет данные локации по её access_key."""
        pass

    @abstractmethod
    async def delete(self, access_key: str) -> bool:
        """Удаляет локацию по её access_key."""
        pass

    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> GameLocation:
        """Создает или обновляет локацию, используя UPSERT по access_key."""
        pass

    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет локации."""
        pass