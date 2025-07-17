import inject
import logging
from typing import Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession

# --- Импорты ---
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

# --- Импортируем правильный DTO для результата ---
from game_server.contracts.dtos.system.commands import LogoutCharacterCommandDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO

class LogoutCharacterHandler(ISystemServiceHandler):
    """
    Обработчик на стороне бэкенда для команды выхода персонажа из игры.
    """
    @inject.autoparams()
    def __init__(
        self,
        char_repo_factory: Callable[[AsyncSession], ICharacterRepository],
        session_factory: Callable[[], AsyncSession],
        logger: logging.Logger
    ):
        self._char_repo_factory = char_repo_factory
        self._session_factory = session_factory
        self._logger = logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, command_dto: LogoutCharacterCommandDTO) -> BaseResultDTO:
        """
        Выполняет выход персонажа, реализуя контракт ISystemServiceHandler.
        """
        self.logger.info(f"Обработка выхода для персонажа ID: {command_dto.payload.character_id}")

        async with self._session_factory() as session:
            char_repo = self._char_repo_factory(session)

            # ИЗМЕНЕНО: Имя аргумента 'character_data' изменено на 'update_data'
            await char_repo.update_character(
                character_id=command_dto.payload.character_id,
                update_data={"status": "offline"} # <-- ИСПРАВЛЕНО
            )
            self.logger.info(f"Статус персонажа {command_dto.payload.character_id} успешно изменен на 'offline' в PostgreSQL.")

            # TODO: Реализовать логику сохранения данных из документа MongoDB в PostgreSQL.

            await session.commit()

        return BaseResultDTO(
            correlation_id=command_dto.correlation_id,
            trace_id=command_dto.trace_id,
            span_id=command_dto.span_id,
            success=True,
            message=f"Character {command_dto.payload.character_id} successfully logged out.",
            client_id=command_dto.client_id
        )

