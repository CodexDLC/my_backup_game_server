from abc import ABC, abstractmethod
from typing import Optional

class ISessionManager(ABC):
    """
    Абстрактный интерфейс для менеджера сессий клиентов.
    Теперь универсален для всех типов клиентов (игроков, ботов).

    Определяет контракт для создания, проверки и удаления сессий,
    независимо от конкретной реализации хранилища (Redis, БД и т.д.).
    """

    @abstractmethod
    async def save_session(self, client_id: str, token: str) -> None:
        """
        Сохраняет новую сессию для указанного ID клиента с предоставленным токеном.

        Args:
            client_id (str): Уникальный идентификатор клиента (игрока или бота).
            token (str): Уникальный токен сессии.
        """
        pass

    @abstractmethod
    async def get_player_id_from_session(self, token: str) -> Optional[str]:
        """
        Проверяет токен сессии и возвращает связанный с ним ID клиента.

        Args:
            token (str): Токен сессии для проверки.

        Returns:
            Optional[str]: ID клиента, если токен валиден и активен, иначе None.
        """
        pass

    @abstractmethod
    async def delete_player_session(self, token: str) -> None:
        """
        Удаляет (завершает) сессию по ее токену.

        Args:
            token (str): Токен сессии для удаления.
        """
        pass