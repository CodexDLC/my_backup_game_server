# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_reference_data_cache.py

from abc import ABC, abstractmethod
from typing import Callable, Any, List, Optional, Type, Dict
from sqlalchemy.ext.asyncio import AsyncSession
# CentralRedisClient не импортируется здесь, так как это деталь реализации, а не часть контракта

class IReferenceDataCacheManager(ABC):
    @abstractmethod
    async def _perform_caching(self, redis_key: str, data_list: List[Any], id_field: str): pass

    @abstractmethod
    async def _cache_from_db_with_version_check(
        self, model_manager_class: Type, model_class: Type, redis_key: str, id_field: str, get_all_method_name: str
    ): pass

    @abstractmethod
    async def _cache_item_base_from_yaml(self): pass

    @abstractmethod
    async def cache_all_reference_data(self) -> bool: pass