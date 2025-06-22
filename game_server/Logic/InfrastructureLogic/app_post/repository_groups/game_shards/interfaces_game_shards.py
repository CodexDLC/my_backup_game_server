# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/game_shards/interfaces_game_shards.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
# Импорт моделей, используемых в сигнатурах этого интерфейса
from game_server.database.models.models import GameShard


class IGameShardRepository(ABC):
    @abstractmethod
    async def create_shard(self, shard_name: str, discord_guild_id: int, max_players: int, is_admin_enabled: bool, is_system_active: bool) -> GameShard: pass
    @abstractmethod
    async def get_shard_by_guild_id(self, discord_guild_id: int) -> Optional[GameShard]: pass
    @abstractmethod
    async def get_shard_by_name(self, shard_name: str) -> Optional[GameShard]: pass
    @abstractmethod
    async def get_all_shards(self) -> List[GameShard]: pass
    @abstractmethod
    async def get_active_available_shards(self, max_players_from_settings: int) -> List[GameShard]: pass
    @abstractmethod
    async def update_shard_state(self, shard_id: int, updates: Dict[str, Any]) -> Optional[GameShard]: pass
    @abstractmethod
    async def increment_current_players(self, discord_guild_id: int) -> Optional[GameShard]: pass
    @abstractmethod
    async def decrement_current_players(self, discord_guild_id: int) -> Optional[GameShard]: pass
    @abstractmethod
    async def update_current_players_sync(self, discord_guild_id: int, actual_count: int) -> Optional[GameShard]: pass
    @abstractmethod
    async def delete_shard(self, shard_id: int) -> bool: pass