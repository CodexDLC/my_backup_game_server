# game_server/Logic/CoreServices/services/identifiers_servise.py

import logging
from typing import Optional

# Зависимость от менеджера репозиториев, а не от сессии
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

logger = logging.getLogger(__name__)

class IdentifiersServise:
    """
    Класс для поиска ID по внешним идентификаторам.
    Работает через RepositoryManager, следуя новому архитектурному паттерну.
    """

    def __init__(self, repository_manager: RepositoryManager):
        """
        Принимает менеджер репозиториев для доступа к слою данных.
        """
        self.repo_manager = repository_manager
        self.account_repo = self.repo_manager.account_info
        logger.debug("✨ IdentifiersServise инициализирован с RepositoryManager.")

    async def get_account_id_by_linked_platform(self, platform_name: str, platform_id: str) -> Optional[int]:
        """
        Находит и возвращает account_id по данным из 'linked_platforms'.

        Args:
            platform_name (str): Название платформы (например, 'discord').
            platform_id (str): Уникальный идентификатор на платформе.

        Returns:
            Optional[int]: ID аккаунта, если найден, иначе None.
        """
        # Теперь мы вызываем метод репозитория, который инкапсулирует логику запроса к БД.
        # Этот метод (find_by_linked_platform) должен быть реализован в AccountInfoRepositoryImpl.
        account = await self.account_repo.find_by_linked_platform(platform_name, platform_id)
        
        if account:
            return account.account_id
        return None

    async def get_online_character_id_by_account(self, account_id: int) -> Optional[int]:
        """
        Находит ID персонажа со статусом 'online' для данного account_id.
        """
        if not account_id:
            return None

        # Используем репозиторий персонажей
        character_repo = self.repo_manager.characters
        character = await character_repo.get_online_character_by_account_id(account_id)
        
        if character:
            return character.character_id
        return None