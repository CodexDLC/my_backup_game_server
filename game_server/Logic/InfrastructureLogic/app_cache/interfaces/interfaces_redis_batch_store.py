# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_redis_batch_store.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

class IRedisBatchStore(ABC):
    @abstractmethod
    async def save_batch(self, key_template: str, batch_id: str, batch_data: Dict[str, Any], ttl_seconds: int) -> bool: pass

    @abstractmethod
    async def load_batch(self, key_template: str, batch_id: str) -> Optional[Dict[str, Any]]: pass

    @abstractmethod
    async def increment_field(self, key_template: str, batch_id: str, field: str, increment_by: int = 1) -> Optional[int]: pass

    @abstractmethod
    async def update_fields(self, key_template: str, batch_id: str, fields: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool: pass

    @abstractmethod
    async def delete_batch(self, key_template: str, batch_id: str) -> bool: pass