# game_server/Logic/ApplicationLogic/auth_service/AccountCreation/account_creation_logic.py

import logging
from typing import Dict, Any, Tuple, Callable
from datetime import datetime, timezone
import inject

# Импорты зависимостей
from game_server.Logic.DomainLogic.auth_service_logic.utils.account_helpers import generate_auth_token, generate_next_guest_username
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository, IAccountInfoRepository
from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.shard_management_logic import ShardOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.contracts.dtos.auth.commands import HubRoutingCommandDTO


# Импорты утилит

# Импорт DTO



class AccountCreator:
    """
    Класс для создания новых аккаунтов.
    Теперь зависимости внедряются напрямую через @inject.autoparams.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        # session_factory: Callable[[], AsyncSession], # УДАЛЕНО: Фабрика сессий больше не нужна здесь, так как сессия передается извне
        account_info_repo_factory: Callable[[AsyncSession], IAccountInfoRepository],
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository],
        identifiers_service: IdentifiersServise,
        shard_orchestrator: ShardOrchestrator,
    ):
        self.logger = logger
        # self._session_factory = session_factory # УДАЛЕНО
        self._account_info_repo_factory = account_info_repo_factory
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self.identifiers_service = identifiers_service
        self.shard_orchestrator = shard_orchestrator
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def create_new_discord_account(self, session: AsyncSession, dto: HubRoutingCommandDTO) -> Tuple[int, int]:
        """
        Создает новый аккаунт Discord и связанные игровые данные в рамках переданной сессии.
        Транзакционная граница управляется вызывающим кодом.

        :param session: Активная сессия SQLAlchemy, переданная извне.
        :param dto: DTO команды HubRoutingCommandDTO.
        :return: Кортеж (account_id, assigned_shard_id).
        :raises RuntimeError: Если не удалось назначить шард.
        """
        self.logger.info(f"Начало создания нового аккаунта для discord_id: {dto.payload.discord_user_id} в рамках внешней транзакции.") # <--- ИСПРАВЛЕНО
        
        # Создаем экземпляры репозиториев с активной сессией
        account_info_repo = self._account_info_repo_factory(session)
        account_game_data_repo = self._account_game_data_repo_factory(session)

        # 1. Создание AccountInfo
        all_guest_usernames = await account_info_repo.get_all_guest_usernames()
        username = await generate_next_guest_username(all_guest_usernames)
        
        account_info_data = {
            "username": username,
            "linked_platforms": {"discord": dto.payload.discord_user_id}, # <--- ИСПРАВЛЕНО
            "auth_token": await generate_auth_token()
        }
        new_account_info = await account_info_repo.create_account(account_info_data)
        new_account_id = new_account_info.account_id
        self.logger.debug(f"Создан AccountInfo для аккаунта {new_account_id}.")

        # 2. Создание AccountGameData и назначение шарда
        # Теперь shard_orchestrator должен будет принимать сессию
        assigned_shard_id = await self.shard_orchestrator.get_or_assign_shard_for_account(
            session=session, # <--- ПЕРЕДАЕМ СЕССИЮ
            account_id=new_account_id
        )

        if assigned_shard_id is None:
            self.logger.error(f"Не удалось назначить шард для нового аккаунта {new_account_id}. Отмена операции.")
            # Откат будет выполнен внешним менеджером транзакций
            raise RuntimeError(f"Failed to assign shard for new account {new_account_id}.")

        await account_game_data_repo.create_account_game_data(
            account_id=new_account_id, 
            initial_shard_id=assigned_shard_id
        )
        self.logger.debug(f"Создан AccountGameData для аккаунта {new_account_id} на шарде {assigned_shard_id}.")
        
        # Коммит и откат управляются вызывающим кодом (DiscordHubHandler)
        self.logger.info(f"Операции создания аккаунта {new_account_id} успешно выполнены. Коммит/откат управляется вызывающим.")
        return new_account_id, assigned_shard_id