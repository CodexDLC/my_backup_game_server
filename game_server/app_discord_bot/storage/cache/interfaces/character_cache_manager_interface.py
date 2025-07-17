# character_cache_manager_interface.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class ICharacterCacheManager(ABC):
    """
    Интерфейс для управления кэшем сессий персонажей в Redis.
    """

    @abstractmethod
    async def cache_login_session(
        self,
        character_data: Dict[str, Any],
        user_id: int,
        guild_id: int,
        account_id: int  # <-- ИЗМЕНЕНИЕ: Добавлен account_id
    ) -> None:
        """
        Выполняет полную процедуру кэширования при входе персонажа в игру.
        
        :param character_data: Полный JSON-документ персонажа с бэкенда.
        :param user_id: Discord ID пользователя.
        :param guild_id: ID сервера (гильдии).
        :param account_id: ID игрового аккаунта.
        """
        pass

    @abstractmethod
    async def get_active_character_id(self, user_id: int) -> Optional[int]:
        """
        Возвращает ID активного персонажа для данного пользователя из хэша сессии.
        
        :param user_id: Discord ID пользователя.
        :return: ID активного персонажа или None, если сессии нет.
        """
        pass

    @abstractmethod
    async def get_character_session(self, character_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает полные сессионные данные персонажа из его хэша.
        """
        pass

    @abstractmethod
    async def clear_login_session(self, user_id: int, guild_id: int) -> None:
        """
        Выполняет процедуру очистки кэша при выходе персонажа из игры.
        """
        pass