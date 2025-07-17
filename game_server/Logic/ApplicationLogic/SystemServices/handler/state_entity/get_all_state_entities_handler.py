# game_server/Logic/ApplicationLogic/SystemServices/handler/state_entity/get_all_state_entities_handler.py

import logging
from typing import Dict, Any, List, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository
from game_server.contracts.dtos.state_entity.commands import GetAllStateEntitiesCommand
from game_server.contracts.dtos.state_entity.data_models import StateEntityDTO
from game_server.contracts.dtos.state_entity.results import GetAllStateEntitiesResult
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

class GetAllStateEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для получения списка всех сущностей состояния (StateEntity).
    """
    @inject.autoparams('logger', 'state_entity_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 state_entity_repo_factory: Callable[[AsyncSession], IStateEntityRepository]
                 ):
        self._logger = logger
        self._state_entity_repo_factory = state_entity_repo_factory
        self._logger.info("GetAllStateEntitiesHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: GetAllStateEntitiesCommand) -> BaseResultDTO[GetAllStateEntitiesResult]:
        self.logger.info(f"Получена команда '{command_dto.command}'.")
        
        state_entity_repo = self._state_entity_repo_factory(session)

        try:
            db_entities = await state_entity_repo.get_all()
            
            response_entities = [StateEntityDTO.model_validate(entity.__dict__) for entity in db_entities]

            self.logger.info(f"Найдено {len(response_entities)} сущностей состояния.")
            
            result_data = GetAllStateEntitiesResult(entities=response_entities)
            
            return BaseResultDTO[GetAllStateEntitiesResult](
                correlation_id=command_dto.correlation_id,
                success=True,
                message="Сущности состояния успешно получены.",
                data=result_data,
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении всех сущностей состояния: {e}")
            raise # Перевыбрасываем, чтобы декоратор сделал rollback