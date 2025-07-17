# game_server/Logic/ApplicationLogic/auth_service/Handlers/auth_issue_token_rpc_handler.py

import logging # Убедитесь, что logging импортирован
import os
from typing import Dict, Any, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем наш декоратор и фабрику сессий
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal

# Импортируем зависимости, которые нужны этому обработчику
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository
from game_server.Logic.DomainLogic.auth_service_logic.utils.account_helpers import generate_auth_token

from game_server.config.settings_core import BOT_GATEWAY_SECRET
from game_server.contracts.dtos.auth.commands import IssueAuthTokenRpcCommandDTO
# УДАЛИТЕ ЭТУ СТРОКУ: from game_server.config.logging.logging_setup import app_logger as logger # <-- Прямой импорт логгера


class AuthIssueTokenRpcHandler:
    """
    Обработчик для RPC-команды на выдачу токена аутентификации.
    Работает в рамках транзакции для проверки учетных данных игрока.
    """
    @inject.autoparams( # Оставьте пустым, если все остальные параметры должны быть инжектированы
        'session_manager', # РАСКОММЕНТИРУЙТЕ, если эти зависимости нужны
        'account_info_repo_factory' # РАСКОММЕНТИРУЙТЕ, если эти зависимости нужны
    )
    def __init__(
        self,
        session_manager: ISessionManager, # РАСКОММЕНТИРУЙТЕ
        account_info_repo_factory: Callable[[AsyncSession], IAccountInfoRepository] # РАСКОММЕНТИРУЙТЕ
    ):
        # 1. Сначала инициализируем логгер как атрибут экземпляра
        self.logger = inject.instance(logging.Logger) # <-- ВОЗВРАЩАЕМ ЭТУ СТРОКУ

        # 2. Теперь можно использовать self.logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

        # 3. Инициализируем остальные зависимости
        self.session_manager = session_manager
        self._account_info_repo_factory = account_info_repo_factory

    @transactional(AsyncSessionLocal) # РАСКОММЕНТИРУЙТЕ, если декоратор нужен
    async def process(self, session: AsyncSession, rpc_payload_dto: IssueAuthTokenRpcCommandDTO) -> Dict[str, Any]:
        """
        Выполняет логику выдачи токена.
        """
        client_type = rpc_payload_dto.client_type
        issued_token = None
        client_id_to_save = None

        self.logger.info(f"Запрос на выдачу токена для клиента типа: {client_type}.") # <-- Используем self.logger

        if client_type == "DISCORD_BOT":
            if rpc_payload_dto.bot_secret == BOT_GATEWAY_SECRET and rpc_payload_dto.bot_name:
                issued_token = await generate_auth_token()
                client_id_to_save = f"BOT_{rpc_payload_dto.bot_name}"
            else:
                return {"success": False, "error": "Invalid bot secret or name.", "error_code": "INVALID_BOT_CREDENTIALS"}

        elif client_type == "PLAYER":
            account_info_repo = self._account_info_repo_factory(session)
            username = rpc_payload_dto.username
            password = rpc_payload_dto.password
            
            account = await account_info_repo.get_account_by_username(username)
            # ВАЖНО: здесь должна быть проверка хэша пароля, а не прямое сравнение
            if account and account.password == password:
                issued_token = await generate_auth_token()
                client_id_to_save = account.account_id
            else:
                return {"success": False, "error": "Invalid credentials.", "error_code": "INVALID_PLAYER_CREDENTIALS"}
        else:
            return {"success": False, "error": "Unknown client type.", "error_code": "UNKNOWN_CLIENT_TYPE"}

        if issued_token and client_id_to_save:
            await self.session_manager.save_session(client_id=client_id_to_save, token=issued_token)
            self.logger.info(f"Токен успешно выдан для клиента '{client_id_to_save}'.") # <-- Используем self.logger
            return {"success": True, "token": issued_token, "expires_in": 3600, "error": None}
        else:
            # Эта ветка не должна быть достижима, но на всякий случай
            return {"success": False, "error": "Failed to issue token due to unknown reason.", "error_code": "UNKNOWN_ISSUE_FAILURE"}