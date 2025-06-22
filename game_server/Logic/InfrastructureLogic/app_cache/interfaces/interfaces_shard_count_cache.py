# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_shard_count_cache.py

from abc import ABC, abstractmethod

class IShardCountCacheManager(ABC):
    """
    Интерфейс для менеджера кэша счетчиков игроков на шарадах.
    Определяет методы, которые должна реализовать конкретная имплементация.
    """

    @abstractmethod
    async def get_shard_player_count(self, discord_guild_id: int) -> int:
        """Получает текущее количество игроков для заданного шарда из Redis."""
        pass

    @abstractmethod
    async def increment_shard_player_count(self, discord_guild_id: int) -> int:
        """Атомарно инкрементирует счетчик игроков для заданного шарда в Redis."""
        pass

    @abstractmethod
    async def decrement_shard_player_count(self, discord_guild_id: int) -> int:
        """Атомарно декрементирует счетчик игроков для заданного шарда в Redis."""
        pass

    @abstractmethod
    async def set_shard_player_count(self, discord_guild_id: int, count: int):
        """Устанавливает счетчик игроков для заданного шарда в Redis до определенного значения."""
        pass

    @abstractmethod
    async def delete_shard_player_count(self, discord_guild_id: int):
        """Удаляет счетчик игроков для заданного шарда из Redis."""
        pass