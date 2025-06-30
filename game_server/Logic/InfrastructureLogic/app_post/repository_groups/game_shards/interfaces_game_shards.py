from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any # Убедитесь, что Dict и Any импортированы, т.к. они используются в upsert_shard

from game_server.database.models.models import GameShard # Импорт вашей модели GameShard

class IGameShardRepository(ABC):
    @abstractmethod
    async def create_shard(self, shard_name: str, discord_guild_id: int, max_players: int, is_admin_enabled: bool, is_system_active: bool) -> GameShard: pass
    
    # 🔥 НОВЫЙ АБСТРАКТНЫЙ МЕТОД: upsert_shard
    @abstractmethod
    async def upsert_shard(self, shard_data: Dict[str, Any]) -> GameShard: pass # Добавляем этот метод в интерфейс

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
