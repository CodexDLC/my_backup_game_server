# Discord_API/core/app_cache_discord/interfaces/player_session_manager_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IPlayerSessionManager(ABC): # 🔥 Класс переименован
    """
    Интерфейс для менеджера кэша, управляющего "живыми" сессиями игроков на шарде.
    """

    @abstractmethod
    async def set_player_session(
        self, 
        guild_id: int, 
        account_id: int,
        session_data: Dict[str, Any]
    ) -> None:
        """Сохраняет или обновляет данные сессии для конкретного игрока."""
        pass

    @abstractmethod
    async def get_player_session(
        self, 
        guild_id: int, 
        account_id: int
    ) -> Optional[Dict[str, Any]]:
        """Извлекает данные сессии конкретного игрока."""
        pass

    @abstractmethod
    async def get_all_sessions(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Извлекает все активные сессии на шарде."""
        pass

    @abstractmethod
    async def delete_player_session(
        self, 
        guild_id: int, 
        account_id: int
    ) -> None:
        """Удаляет данные сессии игрока из кэша."""
        pass