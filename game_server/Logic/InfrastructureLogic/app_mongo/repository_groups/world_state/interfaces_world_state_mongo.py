# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/world_state/interfaces_world_state_mongo.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IWorldStateMongoRepository(ABC):
    @abstractmethod
    async def upsert_locations_with_connections(self, documents: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    async def delete_all_locations(self) -> None:
        pass

    # Добавьте другие методы, которые могут потребоваться (например, get_location_by_id)
    # @abstractmethod
    # async def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
    #     pass