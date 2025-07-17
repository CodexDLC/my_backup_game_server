# game_server/app_discord_bot/storage/cache/interfaces/account_data_manager_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IAccountDataManager(ABC):
    """
    Интерфейс для менеджера кэша, управляющего постоянными данными игровых аккаунтов.
    """

    @abstractmethod
    async def save_account_field(self, shard_id: int, discord_user_id: int, field_name: str, data: Dict[str, Any]) -> None:
        """
        Сохраняет или обновляет одно поле в хеше данных аккаунта, идентифицируемом по discord_user_id.
        """
        pass

    @abstractmethod
    async def get_account_field(self, shard_id: int, discord_user_id: int, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает одно поле из хеша данных аккаунта, идентифицируемого по discord_user_id.
        """
        pass

    @abstractmethod
    async def get_all_account_data(self, shard_id: int, discord_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Извлекает все данные для конкретного аккаунта (все поля хеша),
        идентифицируемого по discord_user_id.
        """
        pass

    @abstractmethod
    async def delete_account_data(self, shard_id: int, discord_user_id: int) -> None:
        """
        Полностью удаляет хеш данных аккаунта из Redis, идентифицируемый по discord_user_id.
        """
        pass
    
    @abstractmethod
    async def get_account_id_by_discord_id(self, discord_user_id: int) -> Optional[int]:
        """
        Извлекает account_id из глобального Redis Hash (поле 'account_id') по Discord User ID.
        :param discord_user_id: Discord User ID игрока.
        :return: account_id или None, если не найден.
        """
        pass

    @abstractmethod
    async def set_discord_account_mapping(self, discord_user_id: int, account_id: int) -> None:
        """
        Сохраняет соответствие Discord User ID к account_id в глобальном Redis Hash (поле 'account_id').
        :param discord_user_id: Discord User ID игрока.
        :param account_id: account_id игрока.
        """
        pass

    # 👇 ДОБАВЛЯЕМ ЭТИ ДВА МЕТОДА
    
    @abstractmethod
    async def set_active_session(self, discord_id: int, account_id: int, character_id: int) -> None:
        """
        Сохраняет ID аккаунта и персонажа в хэш активной сессии.
        """
        pass

    @abstractmethod
    async def get_active_session(self, discord_id: int) -> Optional[Dict[str, int]]:
        """
        Получает ID аккаунта и персонажа из хэша активной сессии.
        """
        pass