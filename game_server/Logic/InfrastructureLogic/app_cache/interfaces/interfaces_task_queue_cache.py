# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_task_queue_cache.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class ITaskQueueCacheManager(ABC):
    @abstractmethod
    async def add_task_to_queue(self, batch_id: str, key_template: str, specs: List[Dict[str, Any]],
                                target_count: int, initial_status: str = "pending") -> bool: pass

    @abstractmethod
    async def get_task_batch_specs(self, batch_id: str, key_template: str, log_prefix: str) -> Optional[List[Dict[str, Any]]]: pass

    @abstractmethod
    async def update_task_status(self, batch_id: str, key_template: str, status: str, log_prefix: str,
                                 error_message: Optional[str] = None, ttl_seconds: Optional[int] = None,
                                 final_generated_count: Optional[int] = None) -> None: pass

    @abstractmethod
    async def get_character_task_specs(self, batch_id: str, key_template: str) -> Tuple[Optional[List], int, Optional[str]]: pass

    @abstractmethod
    async def increment_task_generated_count(self, batch_id: str, key_template: str, increment_by: int = 1) -> Optional[int]: pass

    @abstractmethod
    async def set_character_task_final_status(self, batch_id: str, key_template: str, status: str, **kwargs): pass