# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_character_cache.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ICharacterCacheManager(ABC):
    @abstractmethod
    async def get_character_snapshot(self, character_id: str) -> Optional[Dict[str, Any]]: pass

    @abstractmethod
    async def set_character_snapshot(self, character_id: str, snapshot_data: Dict[str, Any], is_online: bool = True): pass

    @abstractmethod
    async def delete_character_snapshot(self, character_id: str): pass

    @abstractmethod
    async def update_character_snapshot_ttl(self, character_id: str, is_online: bool = True): pass

    @abstractmethod
    async def get_character_id_by_discord_id(self, discord_user_id: str) -> Optional[str]: pass

    @abstractmethod
    async def set_character_id_for_discord_id(self, discord_user_id: str, character_id: str, ttl_seconds: Optional[int] = None): pass

    @abstractmethod
    async def delete_character_id_for_discord_id(self, discord_user_id: str): pass

    @abstractmethod
    async def decrement_pool_count(self) -> int: pass

    @abstractmethod
    async def get_pool_count(self) -> int: pass