# game_server/Logic/CoreServices/services/identifiers_servise.py

import logging
from typing import Optional, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем интерфейсы конкретных репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository


class IdentifiersServise:
    """
    Класс для поиска ID по внешним идентификаторам.
    Теперь методы принимают активную сессию извне и не управляют транзакцией самостоятельно.
    """
    @inject.autoparams()
    def __init__(
        self, 
        logger: logging.Logger,
        # session_factory: Callable[[], AsyncSession], # УДАЛЕНО: Фабрика сессий больше не нужна здесь
        account_info_repo_factory: Callable[[AsyncSession], IAccountInfoRepository],
        character_repo_factory: Callable[[AsyncSession], ICharacterRepository],
    ):
        self.logger = logger
        # self._session_factory = session_factory # УДАЛЕНО
        self._account_info_repo_factory = account_info_repo_factory
        self._character_repo_factory = character_repo_factory

        self.logger.debug("✨ IdentifiersServise инициализирован с прямыми репозиториями.")

    async def get_account_id_by_linked_platform(self, session: AsyncSession, platform_name: str, platform_id: str) -> Optional[int]:
        """
        Находит и возвращает account_id по данным из 'linked_platforms'.
        Выполняется в рамках переданной сессии.
        """
        self.logger.debug(f"Поиск account_id по платформе '{platform_name}' (ID: {platform_id}) в рамках внешней транзакции.")
        account_info_repo = self._account_info_repo_factory(session)

        account = await account_info_repo.get_account_by_identifier(platform_name, platform_id)
        
        # Коммит и откат управляются вызывающим кодом.
        
        if account:
            self.logger.debug(f"Найден account_id: {account.account_id} для платформы '{platform_name}'.")
            return account.account_id
        self.logger.debug(f"Account_id не найден для платформы '{platform_name}' (ID: {platform_id}).")
        return None

    async def get_online_character_id_by_account(self, session: AsyncSession, account_id: int) -> Optional[int]:
        """
        Находит ID персонажа со статусом 'online' для данного account_id.
        Выполняется в рамках переданной сессии.
        """
        if not account_id:
            self.logger.warning("Попытка получить online_character_id для пустого account_id.")
            return None

        self.logger.debug(f"Поиск online_character_id для account_id: {account_id} в рамках внешней транзакции.")
        character_repo = self._character_repo_factory(session)

        character = await character_repo.get_online_character_by_account_id(account_id)
        
        # Коммит и откат управляются вызывающим кодом.

        if character:
            self.logger.debug(f"Найден online_character_id: {character.character_id} для account_id: {account_id}.")
            return character.character_id
        self.logger.debug(f"Online_character_id не найден для account_id: {account_id}.")
        return None