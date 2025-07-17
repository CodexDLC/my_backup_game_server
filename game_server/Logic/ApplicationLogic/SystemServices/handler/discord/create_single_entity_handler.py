# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/create_single_entity_handler.py

import logging
from typing import Dict, Any, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

# 👇 ИЗМЕНЕНИЕ: Импортируем фабрику сессий и декоратор
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импортируем интерфейс репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

# Импортируем DTO и интерфейс обработчика

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.contracts.dtos.discord.commands import DiscordEntityCreateCommand
from game_server.contracts.dtos.discord.data_models import DiscordEntityDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO

class CreateSingleEntityHandler(ISystemServiceHandler):
    """
    Обработчик для создания одной сущности Discord в БД. Работает в рамках транзакции.
    """
    # 👇 ИЗМЕНЕНИЕ: Внедряем логгер и фабрику репозитория
    @inject.autoparams('logger', 'discord_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 discord_repo_factory: Callable[[AsyncSession], IDiscordEntityRepository]
                 ):
        self._logger = logger
        self._discord_repo_factory = discord_repo_factory
        self._logger.info("CreateSingleEntityHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    # 👇 ИЗМЕНЕНИЕ: Делаем метод транзакционным
    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: DiscordEntityCreateCommand) -> BaseResultDTO[DiscordEntityDTO]:
        guild_id = command_dto.guild_id
        discord_id = command_dto.discord_id

        self.logger.info(f"Получена команда '{command_dto.command}' для сущности с Discord ID: {discord_id}.")

        # Создаем репозиторий с активной сессией
        discord_entity_repo = self._discord_repo_factory(session)
        
        try:
            existing_entity = await discord_entity_repo.get_discord_entity_by_discord_id(
                guild_id=guild_id,
                discord_id=discord_id
            )

            if existing_entity:
                self.logger.warning(f"Сущность с Discord ID {discord_id} уже существует. Новая не создавалась.")
                return BaseResultDTO[DiscordEntityDTO](
                    correlation_id=command_dto.correlation_id,
                    success=True,
                    message="Сущность уже существует.",
                    data=DiscordEntityDTO.model_validate(existing_entity.__dict__)
                )

            new_entity_data = command_dto.model_dump(exclude={"command", "correlation_id", "trace_id", "span_id", "client_id"})
            new_db_entity = await discord_entity_repo.create_discord_entity(new_entity_data)

            self.logger.info(f"Сущность '{new_db_entity.name}' (Discord ID: {new_db_entity.discord_id}) успешно создана.")

            return BaseResultDTO[DiscordEntityDTO](
                correlation_id=command_dto.correlation_id,
                success=True,
                message="Сущность успешно создана.",
                data=DiscordEntityDTO.model_validate(new_db_entity.__dict__)
            )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при создании сущности с Discord ID {discord_id}: {e}")
            return BaseResultDTO[DiscordEntityDTO](
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data=None
            )