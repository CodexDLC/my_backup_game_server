# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/character_cache/interfaces_character_cache_mongo.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IMongoCharacterCacheRepository(ABC):
    """
    Интерфейс для репозитория, управляющего документами персонажей в "тёплом кэше" MongoDB.
    """

    @abstractmethod
    async def get_character_by_id(self, character_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает документ персонажа из кэша по его ID.

        :param character_id: Уникальный ID персонажа.
        :return: Словарь с данными персонажа или None, если не найден.
        """
        pass

    @abstractmethod
    async def upsert_character(self, character_document: Dict[str, Any]) -> None:
        """
        Создает новый или полностью обновляет существующий документ персонажа в кэше.
        Документ должен содержать поле '_id', равное character_id.

        :param character_document: Словарь, представляющий полный документ персонажа.
        """
        pass

    @abstractmethod
    async def delete_character(self, character_id: int) -> bool:
        """
        Удаляет документ персонажа из кэша по ID.

        :param character_id: Уникальный ID персонажа.
        :return: True, если удаление успешно, иначе False.
        """
        pass