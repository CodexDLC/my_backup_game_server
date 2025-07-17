# game_server/app_discord_bot/storage/cache/interfaces/game_world_data_manager_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IGameWorldDataManager(ABC):
    """
    Интерфейс для менеджера данных игрового мира в Redis.
    Определяет контракты для работы как со статическими, так и с динамическими данными мира.
    """
    @abstractmethod
    async def set_hash_field(self, key: str, field: str, value: str) -> None:
        """
        Устанавливает значение поля в хеше Redis (для статических данных мира).
        """
        pass

    @abstractmethod
    async def delete_hash(self, key: str) -> None:
        """
        Удаляет весь хеш по заданному ключу.
        """
        pass

    @abstractmethod
    async def get_hash_field(self, key: str, field: str) -> Optional[str]:
        """
        Получает значение поля из хеша (для статических данных мира).
        """
        pass

    @abstractmethod
    async def get_all_hash_fields(self, key: str) -> Dict[str, str]:
        """
        Получает все поля и значения из хеша (для статических данных мира).
        """
        pass

    @abstractmethod
    async def set_dynamic_location_data(self, location_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """
        Сохраняет динамические данные о локации в Redis в виде JSON-строки.
        """
        pass

    @abstractmethod
    async def get_dynamic_location_data(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает динамические данные о локации из Redis.
        """
        pass