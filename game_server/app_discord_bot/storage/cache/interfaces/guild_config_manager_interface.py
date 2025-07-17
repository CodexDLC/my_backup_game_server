from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IGuildConfigManager(ABC):
    """
    Интерфейс для менеджера кэша, управляющего конфигурацией гильдий (шардов) в виде Redis Hash.
    """

    @abstractmethod
    async def set_field(self, guild_id: int, field_name: str, data: Any, shard_type: str) -> None:
        """Сохраняет или обновляет одно поле в Hash конфигурации гильдии."""
        pass

    @abstractmethod
    async def get_field(self, guild_id: int, field_name: str, shard_type: str) -> Optional[Any]:
        """Извлекает одно поле из Hash конфигурации гильдии."""
        pass

    @abstractmethod
    async def get_all_fields(self, guild_id: int, shard_type: str) -> Optional[Dict[str, Any]]:
        """Извлекает все поля и их значения из Hash конфигурации гильдии."""
        pass

    @abstractmethod
    async def delete_fields(self, guild_id: int, fields: List[str], shard_type: str) -> None:
        """Удаляет одно или несколько полей из Hash."""
        pass

    @abstractmethod
    async def delete_config(self, guild_id: int, shard_type: str) -> None:
        """Полностью удаляет Hash конфигурации для гильдии."""
        pass
    
    @abstractmethod
    async def add_player_id_to_registered_list(self, guild_id: int, shard_type: str, player_discord_id: str) -> None:
        """
        Атомарно добавляет Discord ID игрока в список зарегистрированных игроков для данного шарда.
        """
        pass