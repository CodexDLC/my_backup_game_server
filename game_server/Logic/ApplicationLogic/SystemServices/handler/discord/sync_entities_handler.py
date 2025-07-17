# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/sync_entities_handler.py

import logging
from typing import Dict, Any, List, Callable
import inject
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

# 👇 ИЗМЕНЕНИЕ: Импортируем фабрику сессий и декоратор
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импортируем интерфейс репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntitySyncRequest
from game_server.contracts.dtos.discord.data_models import DiscordEntityDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO


class SyncDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для синхронизации (создания/обновления) сущностей Discord в БД.
    Работает в рамках одной транзакции.
    """
    # 👇 ИЗМЕНЕНИЕ: Внедряем логгер и фабрику репозитория
    @inject.autoparams('logger', 'discord_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 discord_repo_factory: Callable[[AsyncSession], IDiscordEntityRepository]
                 ):
        self._logger = logger
        self._discord_repo_factory = discord_repo_factory # Сохраняем фабрику
        self._logger.info("SyncDiscordEntitiesHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    # 👇 ИЗМЕНЕНИЕ: Делаем метод транзакционным
    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: UnifiedEntitySyncRequest) -> BaseResultDTO[Dict[str, Any]]:
        created_count = 0
        updated_count = 0
        errors = []
        processed_entities_responses = []

        guild_id = command_dto.guild_id
        entities_data = command_dto.entities_data

        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}.")
        
        # Создаем репозиторий с активной сессией
        discord_entity_repo = self._discord_repo_factory(session)

        try:
            existing_db_entities = await discord_entity_repo.get_discord_entities_by_guild_id(guild_id)
            existing_by_discord_id = {entity.discord_id: entity for entity in existing_db_entities if entity.discord_id}

            for item_command in entities_data:
                discord_id = item_command.discord_id
                item_data_dict = item_command.model_dump(exclude_unset=True)

                if discord_id and discord_id in existing_by_discord_id:
                    try:
                        updated_entity = await discord_entity_repo.update_discord_entity_by_discord_id(
                            guild_id=guild_id,
                            discord_id=discord_id,
                            updates=item_data_dict
                        )
                        if updated_entity:
                            updated_count += 1
                            processed_entities_responses.append(DiscordEntityDTO.model_validate(updated_entity.__dict__).model_dump())
                    except Exception as e:
                        errors.append({"discord_id": discord_id, "error": f"Ошибка обновления: {e}"})
                else:
                    try:
                        new_entity = await discord_entity_repo.create_discord_entity(item_data_dict)
                        created_count += 1
                        processed_entities_responses.append(DiscordEntityDTO.model_validate(new_entity.__dict__).model_dump())
                    except Exception as e:
                        errors.append({"name": item_command.name, "error": f"Ошибка создания: {e}"})

            self.logger.info(f"Синхронизация для гильдии {guild_id} завершена. Создано: {created_count}, Обновлено: {updated_count}.")

            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                success=True,
                message=f"Синхронизация завершена.",
                data={"created_count": created_count, "updated_count": updated_count, "errors": errors, "processed_entities": processed_entities_responses},
                client_id=command_dto.client_id
            )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при синхронизации сущностей для гильдии {guild_id}: {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data={"created_count": 0, "updated_count": 0, "errors": [{"error": f"Критическая ошибка на сервере: {e}"}], "processed_entities": []},
                client_id=command_dto.client_id
            )