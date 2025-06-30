# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_reference_data_reader.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IReferenceDataReader(ABC):

    @abstractmethod
    async def get_weighted_random_id(
        self, redis_key: str, id_field: str, weight_field: str, default_id: Optional[int]
    ) -> Optional[int]: pass

    @abstractmethod
    async def get_all_item_bases(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_materials(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_suffixes(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_modifiers(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_skills(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_background_stories(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_personalities(self) -> Dict[str, Any]: pass

    @abstractmethod
    async def get_all_inventory_rules(self) -> Dict[str, Any]: pass