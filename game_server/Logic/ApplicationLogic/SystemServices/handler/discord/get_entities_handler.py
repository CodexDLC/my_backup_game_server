# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/get_entities_handler.py

import logging
from typing import Dict, Any, List, Optional, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

# 👇 ИЗМЕНЕНИЕ: Импортируем фабрику сессий и декоратор
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импортируем интерфейс репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

from game_server.contracts.api_models.discord.entity_management_requests import GetDiscordEntitiesRequest
from game_server.contracts.dtos.discord.data_models import DiscordEntityDTO
from game_server.contracts.dtos.discord.results import GetDiscordEntitiesResultDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO

class GetDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для получения сущностей Discord из БД. Работает в рамках транзакции.
    """
    # 👇 ИЗМЕНЕНИЕ: Внедряем логгер и фабрику репозитория
    @inject.autoparams('logger', 'discord_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 discord_repo_factory: Callable[[AsyncSession], IDiscordEntityRepository]
                 ):
        self._logger = logger
        self._discord_repo_factory = discord_repo_factory
        self._logger.info("GetDiscordEntitiesHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    # 👇 ИЗМЕНЕНИЕ: Делаем метод транзакционным
    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: GetDiscordEntitiesRequest) -> BaseResultDTO[GetDiscordEntitiesResultDTO]:
        guild_id = command_dto.guild_id
        entity_type = command_dto.entity_type

        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Тип: {entity_type or 'Все'}.")
        
        # Создаем репозиторий с активной сессией
        discord_entity_repo = self._discord_repo_factory(session)

        try:
            if entity_type:
                entities = await discord_entity_repo.get_discord_entities_by_type(guild_id, entity_type)
            else:
                entities = await discord_entity_repo.get_discord_entities_by_guild_id(guild_id)

            # ПРЕДУПРЕЖДЕНИЕ: Убедитесь, что у ORM-модели entity есть метод to_dict() или используйте Pydantic .from_orm()
            entities_data = [DiscordEntityDTO.model_validate(entity.__dict__).model_dump() for entity in entities]
            
            self.logger.info(f"Найдено {len(entities_data)} сущностей для гильдии {guild_id}.")

            result_data_payload = GetDiscordEntitiesResultDTO(entities=entities_data)

            return BaseResultDTO[GetDiscordEntitiesResultDTO](
                correlation_id=command_dto.correlation_id,
                success=True,
                message=f"Найдено {len(entities_data)} сущностей.",
                data=result_data_payload,
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при получении сущностей для гильдии {guild_id}: {e}")
            error_data_payload = GetDiscordEntitiesResultDTO(entities=[])
            return BaseResultDTO[GetDiscordEntitiesResultDTO](
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data=error_data_payload,
                client_id=command_dto.client_id
            )