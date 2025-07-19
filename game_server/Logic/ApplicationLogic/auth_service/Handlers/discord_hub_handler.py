# game_server/Logic/ApplicationLogic/auth_service/Handlers/discord_hub_handler.py

import logging
from typing import Dict, Any, Union, Callable
import inject
from datetime import datetime, timezone # Добавлен timezone
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.contracts.dtos.auth.commands import HubRoutingCommandDTO
from game_server.contracts.dtos.system.results import HubRoutingResultDTO, HubRoutingResultData
from game_server.contracts.shared_models.base_responses import ErrorDetail

from .i_auth_handler import IAuthHandler


from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise
from game_server.Logic.DomainLogic.auth_service_logic.AccountCreation.account_creation_logic import AccountCreator
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.shard_management_logic import ShardOrchestrator
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository


class DiscordHubHandler(IAuthHandler):
    """
    Регистрация аккаунта через дискорд сервер по дискорд айди
    
    """
    @inject.autoparams(
        'session_factory',
        'identifiers_service',
        'account_creator',
        'shard_manager',
        'account_game_data_repo_factory'
    )
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        identifiers_service: IdentifiersServise,
        account_creator: AccountCreator,
        shard_manager: ShardOrchestrator,
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository],
    ):
        self.logger = inject.instance(logging.Logger)
        self._session_factory = session_factory
        self.identifiers_service = identifiers_service
        self.account_creator = account_creator
        self.shard_manager = shard_manager
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self.logger.info("✅ DiscordHubHandler инициализирован.")
        
    async def process(self, dto: HubRoutingCommandDTO) -> Union[HubRoutingResultDTO]:
        self.logger.info(f"Начало процесса маршрутизации для discord_id: {dto.payload.discord_user_id} (Correlation ID: {dto.correlation_id})")

        try:
            account_id = None
            assigned_shard_id = None

            async with self._session_factory() as session:
                account_game_data_repo = self._account_game_data_repo_factory(session)

                # Шаг 1: Поиск существующего аккаунта
                account_id = await self.identifiers_service.get_account_id_by_linked_platform(
                    session=session, # <--- ПЕРЕДАЕМ СЕССИЮ СЮДА!
                    platform_name='discord',
                    platform_id=dto.payload.discord_user_id
                )

                # Шаг 2: Создание нового аккаунта (если необходимо)
                if not account_id:
                    self.logger.info(f"Аккаунт для discord_id {dto.payload.discord_user_id} не найден. Создание нового. (Correlation ID: {dto.correlation_id})")
                    # Вызов create_new_discord_account теперь должен передавать session
                    account_id, assigned_shard_id = await self.account_creator.create_new_discord_account(session, dto) # <--- ИСПРАВЛЕНИЕ ЗДЕСЬ

                else:
                    self.logger.info(f"Найден существующий аккаунт: {account_id} (Correlation ID: {dto.correlation_id})")
                    account_game_data = await account_game_data_repo.get_account_game_data(account_id)

                    if account_game_data is None:
                        self.logger.warning(f"AccountGameData не найдена для существующего account_id: {account_id}. Попытка создания. (Correlation ID: {dto.correlation_id})")
                        try:
                            account_game_data = await account_game_data_repo.create_account_game_data(account_id=account_id) # <--- Возможно, здесь тоже нужна сессия, если create_account_game_data ее принимает
                            if account_game_data:
                                self.logger.info(f"AccountGameData успешно создана для account_id: {account_id}. (Correlation ID: {dto.correlation_id})")
                            else:
                                msg = f"Не удалось создать AccountGameData для существующего account_id: {account_id} после попытки. (Correlation ID: {dto.correlation_id})"
                                self.logger.critical(msg)
                                return HubRoutingResultDTO(
                                    correlation_id=dto.correlation_id,
                                    trace_id=dto.trace_id,
                                    span_id=dto.span_id,
                                    success=False,
                                    message=msg,
                                    error=ErrorDetail(code="ACCOUNT_GAME_DATA_CREATION_FAILED", message=msg).model_dump()
                                )
                        except Exception as create_e:
                            msg = f"Ошибка при попытке создания AccountGameData для account_id: {account_id}: {create_e}. (Correlation ID: {dto.correlation_id})"
                            self.logger.critical(msg, exc_info=True)
                            return HubRoutingResultDTO(
                                correlation_id=dto.correlation_id,
                                trace_id=dto.trace_id,
                                span_id=dto.span_id,
                                success=False,
                                message=msg,
                                error=ErrorDetail(code="ACCOUNT_GAME_DATA_CREATION_EXCEPTION", message=msg).model_dump()
                            )

                    if account_game_data.shard_id is None:
                        self.logger.info(f"Аккаунт {account_id} без прописки. Назначение нового шарда. (Correlation ID: {dto.correlation_id})")
                        assigned_shard_id = await self.shard_manager.get_or_assign_shard_for_account(
                            session=session, # <--- ПЕРЕДАЕМ СЕССИЮ СЮДА!
                            account_id=account_id
                        )
                        if assigned_shard_id is None:
                            msg = f"Не удалось назначить шард для игрока {account_id} после попытки повторной прописки (Correlation ID: {dto.correlation_id})."
                            self.logger.error(msg)
                            return HubRoutingResultDTO(
                                correlation_id=dto.correlation_id,
                                trace_id=dto.trace_id,
                                span_id=dto.span_id,
                                success=False,
                                message=msg,
                                error=ErrorDetail(code="SHARD_ASSIGNMENT_FAILED_REPROVISION", message=msg).model_dump()
                            )
                        account_game_data.shard_id = assigned_shard_id
                        account_game_data.last_login_game = datetime.now(timezone.utc)
                        await account_game_data_repo.update_shard_id(account_id, assigned_shard_id)
                        await account_game_data_repo.update_last_login_game(account_id) # <--- Возможно, здесь тоже нужна сессия
                        self.logger.info(f"Игроку {account_id} назначена новая прописка на шард: {assigned_shard_id} (Correlation ID: {dto.correlation_id})")
                    else:
                        assigned_shard_id = account_game_data.shard_id
                        self.logger.info(f"Аккаунт {account_id} уже имеет прописку на шарде: {assigned_shard_id} (Correlation ID: {dto.correlation_id})")
                        await account_game_data_repo.update_last_login_game(account_id) # <--- Возможно, здесь тоже нужна сессия

                if assigned_shard_id is None:
                    msg = f"Не удалось определить шард для игрока {account_id}. (Correlation ID: {dto.correlation_id})."
                    self.logger.error(msg)
                    return HubRoutingResultDTO(
                        correlation_id=dto.correlation_id,
                        trace_id=dto.trace_id,
                        span_id=dto.span_id,
                        success=False,
                        message=msg,
                        error=ErrorDetail(code="SHARD_ASSIGNMENT_FAILED_UNKNOWN", message=msg).model_dump()
                    )

                self.logger.info(f"Игроку {account_id} обработана прописка на шард: {assigned_shard_id} (Correlation ID: {dto.correlation_id})")

                await session.commit()
                self.logger.info(f"Транзакция для DiscordHubHandler для аккаунта {account_id} успешно закоммичена.")

                return HubRoutingResultDTO(
                    correlation_id=dto.correlation_id,
                    trace_id=dto.trace_id,
                    span_id=dto.span_id,
                    success=True,
                    message="Маршрутизация успешно выполнена.",
                    data=HubRoutingResultData(account_id=account_id, shard_id=assigned_shard_id)
                )

        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при маршрутизации для discord_id {dto.payload.discord_user_id} (Correlation ID: {dto.correlation_id})")
            
            if session.in_transaction():
                await session.rollback()
            
            return HubRoutingResultDTO(
                correlation_id=dto.correlation_id,
                trace_id=dto.trace_id,
                span_id=dto.span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {str(e)}",
                error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(e)).model_dump()
            )