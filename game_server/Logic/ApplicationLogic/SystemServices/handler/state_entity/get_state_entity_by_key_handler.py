# game_server/Logic/ApplicationLogic/SystemServices/handler/state_entity/get_state_entity_by_key_handler.py

import logging
from typing import Dict, Any, Optional, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository
from game_server.contracts.dtos.state_entity.commands import GetStateEntityByKeyCommand
from game_server.contracts.dtos.state_entity.data_models import StateEntityDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler


class GetStateEntityByKeyHandler(ISystemServiceHandler):
    """
    Обработчик для получения одной сущности состояния (StateEntity) по ее уникальному ключу.
    """
    @inject.autoparams('logger', 'state_entity_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 state_entity_repo_factory: Callable[[AsyncSession], IStateEntityRepository]
                 ):
        self._logger = logger
        self._state_entity_repo_factory = state_entity_repo_factory
        self._logger.info("GetStateEntityByKeyHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: GetStateEntityByKeyCommand) -> BaseResultDTO[Optional[StateEntityDTO]]:
        key = command_dto.access_code
        self.logger.info(f"Получена команда '{command_dto.command}' для ключа '{key}'.")
        
        state_entity_repo = self._state_entity_repo_factory(session)

        try:
            entity = await state_entity_repo.get_state_entity_by_key(key)

            if entity:
                self.logger.info(f"Сущность состояния для ключа '{key}' найдена.")
                return BaseResultDTO[StateEntityDTO](
                    correlation_id=command_dto.correlation_id,
                    success=True,
                    message=f"Сущность с ключом '{key}' успешно найдена.",
                    data=StateEntityDTO.model_validate(entity.__dict__),
                    client_id=command_dto.client_id
                )
            else:
                self.logger.warning(f"Сущность состояния для ключа '{key}' не найдена.")
                return BaseResultDTO[Optional[StateEntityDTO]](
                    correlation_id=command_dto.correlation_id,
                    success=False,
                    message=f"Сущность с ключом '{key}' не найдена.",
                    data=None,
                    client_id=command_dto.client_id
                )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении сущности состояния по ключу '{key}': {e}")
            raise