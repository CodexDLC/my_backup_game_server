# game_server/Logic/ApplicationLogic/SystemServices/handler/state_entity/get_state_entity_by_key_handler.py

from typing import Dict, Any, Optional # Добавлен Optional
# ИСПРАВЛЕНИЕ: Добавлены импорты StateEntityResult, StateEntityDTO и BaseResultDTO
from game_server.common_contracts.dtos.state_entity_dtos import GetStateEntityByKeyCommand, StateEntityResult, StateEntityDTO
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO


from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler


class GetStateEntityByKeyHandler(ISystemServiceHandler):
    """
    Обработчик для получения одной сущности состояния (StateEntity) по ее уникальному ключу.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.state_entity_repo = self.repo_manager.state_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    # ИСПРАВЛЕНИЕ: Изменен возвращаемый тип на BaseResultDTO[StateEntityDTO]
    async def process(self, command_dto: GetStateEntityByKeyCommand) -> BaseResultDTO[Optional[StateEntityDTO]]:
        """
        Выполняет логику получения одной сущности состояния по ключу.
        """
        key = command_dto.access_code # ИСПРАВЛЕНИЕ: Используем access_code, а не key
        self.logger.info(f"Получена команда '{command_dto.command}' для ключа '{key}'.")

        try:
            # 1. Вызываем метод репозитория
            entity = await self.state_entity_repo.get_state_entity_by_key(key)

            if entity:
                # 2. Если сущность найдена, возвращаем ее с успехом
                self.logger.info(f"Сущность состояния для ключа '{key}' найдена.")
                # ИСПРАВЛЕНИЕ: Формируем BaseResultDTO с StateEntityDTO в поле data
                return BaseResultDTO[StateEntityDTO](
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=True,
                    message=f"Сущность с ключом '{key}' успешно найдена.",
                    data=StateEntityDTO.model_validate(entity.__dict__), # Передаем сконвертированный DTO
                    client_id=command_dto.client_id
                )
            else:
                # 3. Если не найдена, возвращаем неуспех
                self.logger.warning(f"Сущность состояния для ключа '{key}' не найдена.")
                # ИСПРАВЛЕНИЕ: Формируем BaseResultDTO с success=False и data=None
                return BaseResultDTO[Optional[StateEntityDTO]](
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=False,
                    message=f"Сущность с ключом '{key}' не найдена.",
                    data=None, # Данных нет
                    client_id=command_dto.client_id
                )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении сущности состояния по ключу '{key}': {e}")
            # ИСПРАВЛЕНИЕ: Формируем BaseResultDTO с ошибкой
            return BaseResultDTO[Optional[StateEntityDTO]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data=None, # Данных нет при ошибке
                client_id=command_dto.client_id
            )
