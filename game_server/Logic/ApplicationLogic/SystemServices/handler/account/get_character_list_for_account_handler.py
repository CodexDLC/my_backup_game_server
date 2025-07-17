# game_server\Logic\ApplicationLogic\SystemServices\handler\account\get_character_list_for_account_handler.py

import logging
from typing import Dict, Any, List, Union, Callable
import inject
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

# НОВОЕ: Импортируем фабрику сессий и декоратор transactional
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.contracts.api_models.character.responses import CharacterListResponseData, GetCharacterListForAccountResultDTO
from game_server.contracts.dtos.character.data_models import CharacterDTO
from game_server.contracts.dtos.system.commands import GetCharacterListForAccountCommandDTO

from game_server.contracts.dtos.system.results import HubRoutingResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail


# Импорт интерфейсов репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeRepository
from game_server.database.models.models import Character


class GetCharacterListForAccountHandler(ISystemServiceHandler):
    """
    Обработчик для получения списка персонажей аккаунта и обновления времени его последнего логина.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository],
        character_repo_factory: Callable[[AsyncSession], ICharacterRepository],
        creature_repo_factory: Callable[[AsyncSession], ICreatureTypeRepository],
    ):
        self._logger = logger
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self._character_repo_factory = character_repo_factory
        self._creature_repo_factory = creature_repo_factory
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @transactional(AsyncSessionLocal)
    # 🔥 ИЗМЕНЕНО: command_dto остается позиционным
    async def process(self, session: AsyncSession, command_dto: GetCharacterListForAccountCommandDTO) -> Union[GetCharacterListForAccountResultDTO, HubRoutingResultDTO]:
        self._logger.info(f"Начало обработки запроса списка персонажей для account_id: {command_dto.account_id} (Correlation ID: {command_dto.correlation_id})")

        try:
            account_game_data_repo = self._account_game_data_repo_factory(session)
            character_repo = self._character_repo_factory(session)
            creature_repo = self._creature_repo_factory(session)

            updated_game_data = await account_game_data_repo.update_last_login_game(
                account_id=command_dto.account_id
            )
            
            if not updated_game_data:
                msg = f"Не удалось обновить last_login_game для аккаунта {command_dto.account_id}. Возможно, AccountGameData не существует."
                self._logger.warning(msg)
                return HubRoutingResultDTO(
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=False,
                    message=msg,
                    error=ErrorDetail(code="ACCOUNT_GAME_DATA_NOT_FOUND", message=msg).model_dump()
                )
            self._logger.info(f"Время последнего входа для аккаунта {command_dto.account_id} обновлено.")

            raw_characters: List[Character] = await character_repo.get_characters_by_account_id(
                account_id=command_dto.account_id
            )
            
            characters_dto: List[CharacterDTO] = []
            for char in raw_characters:
                characters_dto.append(CharacterDTO(
                    character_id=char.character_id,
                    name=char.name,
                    surname=char.surname,
                    creature_type_id=char.creature_type_id,
                    status=char.status,
                    clan_id=char.clan_id
                ))
            
            self._logger.info(f"Для аккаунта {command_dto.account_id} найдено {len(characters_dto)} персонажей.")

            self._logger.info(f"Операция получения списка персонажей для аккаунта {command_dto.account_id} успешно завершена (коммит будет извне).")

            return GetCharacterListForAccountResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message="Данные о персонажах успешно загружены.",
                data=CharacterListResponseData(characters=characters_dto),
                client_id=command_dto.client_id # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
            )

        except Exception as e:
            self._logger.exception(f"Непредвиденная ошибка при обработке запроса списка персонажей для account_id {command_dto.account_id} (Correlation ID: {command_dto.correlation_id})")         
        
            return HubRoutingResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {str(e)}",
                error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(e)).model_dump(),
                client_id=command_dto.client_id # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
            )