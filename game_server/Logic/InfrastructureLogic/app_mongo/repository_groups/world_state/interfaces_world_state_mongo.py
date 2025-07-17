# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/world_state/interfaces_world_state_mongo.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pymongo.results import BulkWriteResult

# --- ОБНОВЛЕННЫЙ ИНТЕРФЕЙС ДЛЯ РЕГИОНОВ МИРА ---

class IWorldStateRepository(ABC):
    """
    Интерфейс для репозитория, работающего со статическими регионами мира (коллекция static_world_regions).
    """
    @abstractmethod
    async def get_region_by_id(self, region_id: str) -> Optional[Dict[str, Any]]:
        """Получает один документ-регион по его ID."""
        pass

    @abstractmethod
    async def get_all_regions(self) -> List[Dict[str, Any]]:
        """Получает все документы-регионы из коллекции."""
        pass

    @abstractmethod
    async def save_region(self, region_data: Dict[str, Any]) -> bool:
        """Сохраняет или полностью перезаписывает один регион."""
        pass

    @abstractmethod
    async def bulk_save_regions(self, regions_data: List[Dict[str, Any]]) -> BulkWriteResult:
        """Выполняет пакетное сохранение/обновление нескольких регионов."""
        pass


# --- Интерфейс для "живых" локаций (ДОБАВЛЕН bulk_save_active_locations) ---

class ILocationStateRepository(ABC):
    """
    Интерфейс для репозитория, работающего с состоянием "живых" локаций.
    """
    @abstractmethod
    async def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_all_locations(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def add_player_to_location(self, location_id: str, player_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def remove_player_from_location(self, location_id: str, player_id: str) -> bool:
        pass

    @abstractmethod
    async def bulk_save_active_locations(self, documents: List[Dict[str, Any]]) -> BulkWriteResult: # <--- ДОБАВЛЕНО
        """
        Массово сохраняет (или обновляет) документы активных локаций.
        """
        pass