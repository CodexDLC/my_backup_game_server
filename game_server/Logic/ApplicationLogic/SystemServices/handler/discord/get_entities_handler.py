# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/get_entities_handler.py

import logging
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.common_contracts.api_models.discord_api import GetDiscordEntitiesRequest
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO
from game_server.common_contracts.dtos.discord_dtos import DiscordEntityDTO, GetDiscordEntitiesResultDTO


class GetDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для получения сущностей Discord из БД по гильдии и опциональному типу.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.discord_entity_repo = self.repo_manager.discord_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    async def process(self, command_dto: GetDiscordEntitiesRequest) -> BaseResultDTO[GetDiscordEntitiesResultDTO]:
        guild_id = command_dto.guild_id
        entity_type = command_dto.entity_type

        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Тип сущности: {entity_type or 'Все'}. (Correlation ID: {command_dto.correlation_id})")

        try:
            # Получаем сущности из БД
            if entity_type:
                entities = await self.discord_entity_repo.get_discord_entities_by_type(guild_id, entity_type)
            else:
                entities = await self.discord_entity_repo.get_discord_entities_by_guild_id(guild_id)

            # Преобразуем объекты модели в словари для DTO
            # Предполагаем, что ORM-объекты имеют метод .to_dict() или подобный для сериализации
            entities_data = [entity.to_dict() for entity in entities]
            
            self.logger.info(f"Найдено {len(entities_data)} сущностей для гильдии {guild_id}. (Correlation ID: {command_dto.correlation_id})")

            # ИСПРАВЛЕНИЕ: Создаем GetDiscordEntitiesResultDTO, передавая только его собственные поля.
            # Если GetDiscordEntitiesResultDTO ожидает correlation_id, success, message - это ошибка в его определении в discord_dtos.py
            result_data_payload = GetDiscordEntitiesResultDTO(entities=entities_data)

            # Затем передаем этот созданный DTO в поле 'data' BaseResultDTO.
            return BaseResultDTO[GetDiscordEntitiesResultDTO](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Найдено {len(entities_data)} сущностей.",
                data=result_data_payload, # <-- ИСПРАВЛЕНО: передаем созданный DTO
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении сущностей для гильдии {guild_id} (Correlation ID: {command_dto.correlation_id}): {e}")
            # ИСПРАВЛЕНИЕ: Создаем GetDiscordEntitiesResultDTO (пустой)
            error_data_payload = GetDiscordEntitiesResultDTO(entities=[])
            return BaseResultDTO[GetDiscordEntitiesResultDTO](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data=error_data_payload, # <-- ИСПРАВЛЕНО: передаем созданный DTO
                client_id=command_dto.client_id
            )

