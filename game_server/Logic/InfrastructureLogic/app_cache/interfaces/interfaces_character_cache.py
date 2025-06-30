# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_character_cache.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ICharacterCacheManager(ABC):
    """
    Интерфейс для менеджера кэша, управляющего данными персонажей.
    """

    # 🔥 ИЗМЕНЕНИЕ: Добавлен account_id во все методы для работы со снапшотами
    @abstractmethod
    async def get_character_snapshot(self, account_id: str, character_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def set_character_snapshot(self, account_id: str, character_id: str, snapshot_data: Dict[str, Any], is_online: bool = True):
        pass

    @abstractmethod
    async def delete_character_snapshot(self, account_id: str, character_id: str):
        pass

    @abstractmethod
    async def update_character_snapshot_ttl(self, account_id: str, character_id: str, is_online: bool = True):
        pass

    # Методы для пула персонажей остаются без изменений в сигнатуре
    @abstractmethod
    async def decrement_pool_count(self) -> int:
        pass

    @abstractmethod
    async def get_pool_count(self) -> int:
        pass