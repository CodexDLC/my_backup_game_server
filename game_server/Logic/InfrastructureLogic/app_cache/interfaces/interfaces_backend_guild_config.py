# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_backend_guild_config.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IBackendGuildConfigManager(ABC):
    """
    Интерфейс для менеджера кэша на стороне бэкенда, управляющего
    копией конфигурации гильдий, полученной от Discord-бота.
    """

    @abstractmethod
    async def set_field(self, guild_id: int, field_name: str, data: Any) -> None:
        """Сохраняет или обновляет одно поле в Hash конфигурации гильдии."""
        pass

    @abstractmethod
    async def get_field(self, guild_id: int, field_name: str) -> Optional[Any]:
        """Извлекает одно поле из Hash конфигурации гильдии."""
        pass
    
    @abstractmethod
    async def get_all_fields(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Извлекает все поля из Hash конфигурации гильдии."""
        pass

    @abstractmethod
    async def delete_fields(self, guild_id: int, fields: List[str]) -> None:
        """Удаляет одно или несколько полей из Hash."""
        pass

    @abstractmethod
    async def delete_config(self, guild_id: int) -> None:
        """Полностью удаляет Hash конфигурации для гильдии."""
        pass