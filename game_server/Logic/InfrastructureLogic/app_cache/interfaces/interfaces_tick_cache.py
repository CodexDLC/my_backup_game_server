# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_tick_cache.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class ITickCacheManager(ABC):
    @abstractmethod
    async def add_batch_of_instructions_to_category(self, category: str, batch_id: str, instructions_batch: List[Dict[str, Any]]): pass

    @abstractmethod
    async def get_all_categories_with_batches(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]: pass

    @abstractmethod
    async def get_batch_by_id(self, category: str, batch_id: str) -> Optional[List[Dict[str, Any]]]: pass

    @abstractmethod
    async def remove_batch_by_id(self, category: str, batch_id: str): pass

    @abstractmethod
    async def delete_all_categorized_tasks(self): pass