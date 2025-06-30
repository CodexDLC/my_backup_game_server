from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from game_server.database.models.models import DiscordEntity

class IDiscordEntityRepository(ABC):
    @abstractmethod
    async def create_discord_entity(self, entity_data: Dict[str, Any]) -> DiscordEntity: pass
    @abstractmethod
    async def get_discord_entity_by_discord_id(self, guild_id: int, discord_id: int) -> Optional[DiscordEntity]: pass
    @abstractmethod
    async def get_discord_entity_by_name_and_parent(self, guild_id: int, name: str, parent_id: Optional[int]) -> Optional[DiscordEntity]: pass
    @abstractmethod
    async def get_discord_entities_by_guild_id(self, guild_id: int) -> List[DiscordEntity]: pass
    @abstractmethod
    async def update_discord_entity(self, entity_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]: pass
    @abstractmethod
    async def update_discord_entity_by_discord_id(self, guild_id: int, discord_id: int, updates: Dict[str, Any]) -> Optional[DiscordEntity]: pass
    @abstractmethod
    async def delete_discord_entity_by_id(self, entity_id: int) -> bool: pass
    @abstractmethod
    async def delete_discord_entities_batch(self, guild_id: int, discord_ids: List[int]) -> int: pass
    @abstractmethod
    async def get_total_entities_count(self, guild_id: Optional[int] = None) -> int: pass

