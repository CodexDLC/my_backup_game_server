# game_server/Logic/ApplicationLogic/auth_service/AccountCreation/account_creation_logic.py

import logging
from typing import Dict, Any
from datetime import datetime, timezone

# Импорты зависимостей
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise


# Импорты утилит
from game_server.Logic.ApplicationLogic.auth_service.utils.account_helpers import generate_auth_token, generate_next_guest_username

class AccountCreator:
    """
    Класс для создания новых аккаунтов.
    """
    def __init__(
        self,
        repository_manager: RepositoryManager,
        identifiers_service: IdentifiersServise, # Аргумент, ожидаемый конструктором
    ):
        self.repo_manager = repository_manager
        self.identifiers_service = identifiers_service # Сохраняем как атрибут
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def create_new_discord_account(self, dto: Any) -> Dict[str, Any]:
        self.logger.info(f"Создание нового аккаунта для discord_id: {dto.discord_user_id}")
        
        # 1. Создание AccountInfo
        # Предполагаем, что generate_next_guest_username может использовать self.identifiers_service или self.random_service
        # Если generate_next_guest_username использует только get_all_guest_usernames, то это нормально.
        # Если ему нужна случайность, он должен получить доступ к self.random_service.
        # Я предполагаю, что ему нужен identifiers_service, так как он использует get_all_guest_usernames.
        # И random_service, если generate_auth_token использует случайность.
        
        # Если generate_next_guest_username сам вызывает репозиторий, это может быть неоптимально.
        # Лучше, если он принимает уже готовые данные или сервис.
        # Для этой версии, чтобы не делать слишком много изменений сразу:
        all_guest_usernames = await self.repo_manager.account_info.get_all_guest_usernames()
        username = generate_next_guest_username(all_guest_usernames) # generate_next_guest_username должен работать с Python lists
        
        account_info_data = {
            "username": username,
            "avatar": getattr(dto, 'avatar', None),
            "locale": getattr(dto, 'locale', None),
            "linked_platforms": {"discord": dto.discord_user_id},
            "auth_token": await generate_auth_token() # Возможно, generate_auth_token должен использовать self.random_service?
        }
        new_account_info = await self.repo_manager.account_info.create_account(account_info_data)
        new_account_id = new_account_info.account_id

        # 2. Создание AccountGameData
        account_game_data = {
            "account_id": new_account_id,
            "last_login_game": datetime.now(timezone.utc)
        }
        await self.repo_manager.account_game_data.create_or_update(account_game_data)
        
        self.logger.info(f"Аккаунт {new_account_id} ('{username}') успешно создан.")
        return {"account_id": new_account_id}
