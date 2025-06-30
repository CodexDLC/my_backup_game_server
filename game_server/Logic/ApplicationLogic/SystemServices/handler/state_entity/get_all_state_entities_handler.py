# game_server/Logic/ApplicationLogic/SystemServices/handler/state_entity/get_all_state_entities_handler.py

import logging
from typing import Dict, Any, List, Optional # Добавлен Optional для type hinting

from game_server.common_contracts.dtos.state_entity_dtos import GetAllStateEntitiesCommand, GetAllStateEntitiesResult, StateEntityDTO
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO # Добавлен импорт BaseResultDTO, если он нужен для возвращаемого типа

from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler


class GetAllStateEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для получения списка всех сущностей состояния (StateEntity).
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.state_entity_repo = self.repo_manager.state_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    # РЕФАКТОРИНГ: Возвращаемый тип теперь BaseResultDTO[GetAllStateEntitiesResult]
    async def process(self, command_dto: GetAllStateEntitiesCommand) -> BaseResultDTO[GetAllStateEntitiesResult]:
        """
        Выполняет логику получения списка всех сущностей состояния.
        """
        self.logger.info(f"Получена команда '{command_dto.command}'.")

        try:
            # 1. Вызываем метод репозитория для получения ORM-объектов
            db_entities = await self.state_entity_repo.get_all()
            
            # ВРЕМЕННОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ:
            self.logger.critical(f"ДИАГНОСТИКА: db_entities (получено из репозитория, тип: {type(db_entities)}, длина: {len(db_entities)}): {db_entities}")

            # 2. Конвертируем ORM-объекты в список DTO
            response_entities: List[StateEntityDTO] = [
                StateEntityDTO.model_validate(entity.__dict__) for entity in db_entities
            ]

            # ВРЕМЕННОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ:
            self.logger.critical(f"ДИАГНОСТИКА: response_entities (сконвертировано в DTO, тип: {type(response_entities)}, длина: {len(response_entities)}): {response_entities}")

            self.logger.info(f"Найдено {len(response_entities)} сущностей состояния.")
            
            # РЕФАКТОРИНГ: Возвращаем BaseResultDTO, оборачивая GetAllStateEntitiesResult
            return BaseResultDTO[GetAllStateEntitiesResult](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id, 
                span_id=command_dto.span_id,   
                success=True,
                message="Сущности состояния успешно получены.", 
                data=GetAllStateEntitiesResult(entities=response_entities), # Оборачиваем в GetAllStateEntitiesResult
                client_id=command_dto.client_id 
            )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении всех сущностей состояния: {e}")
            
            # РЕФАКТОРИНГ: Возвращаем BaseResultDTO с ошибкой
            return BaseResultDTO[GetAllStateEntitiesResult](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Ошибка при получении сущностей состояния: {e}",
                data=GetAllStateEntitiesResult(entities=[]), # Возвращаем пустой список в DTO при ошибке
                client_id=command_dto.client_id 
            )
