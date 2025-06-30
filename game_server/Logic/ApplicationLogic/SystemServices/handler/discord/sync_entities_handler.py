# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/sync_entities_handler.py

import logging
import uuid
from typing import Dict, Any, List
from pydantic import ValidationError

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.common_contracts.api_models.discord_api import DiscordEntityDTO, UnifiedEntitySyncRequest
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO # Базовый класс для всех результатов


class SyncDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для синхронизации (создания/обновления) сущностей Discord в БД.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.discord_entity_repo = self.repo_manager.discord_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    async def process(self, command_dto: UnifiedEntitySyncRequest) -> BaseResultDTO[Dict[str, Any]]:
        created_count = 0
        updated_count = 0
        errors = []
        processed_entities_responses = []

        guild_id = command_dto.guild_id
        entities_data = command_dto.entities_data

        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Начинаем синхронизацию. (Correlation ID: {command_dto.correlation_id})")
        self.logger.info(f"SyncDiscordEntitiesHandler: Client ID из command_dto: {command_dto.client_id}") # Добавлен лог для проверки

        try:
            existing_db_entities = await self.repo_manager.discord_entities.get_discord_entities_by_guild_id(guild_id)
            existing_by_discord_id = {entity.discord_id: entity for entity in existing_db_entities if entity.discord_id}

            for item_command in entities_data:
                discord_id = item_command.discord_id
                
                item_data_dict = item_command.model_dump(exclude_unset=True) 

                if discord_id and discord_id in existing_by_discord_id:
                    try:
                        updated_entity = await self.repo_manager.discord_entities.update_discord_entity_by_discord_id(
                            guild_id=guild_id,
                            discord_id=discord_id,
                            updates=item_data_dict
                        )
                        if updated_entity:
                            updated_count += 1
                            processed_entities_responses.append(DiscordEntityDTO.model_validate(updated_entity.__dict__).model_dump())
                    except Exception as e:
                        errors.append({"discord_id": discord_id, "error": f"Ошибка обновления: {e}"})
                        self.logger.warning(f"Ошибка обновления сущности Discord ID {discord_id}: {e}")

                else:
                    try:
                        new_entity = await self.repo_manager.discord_entities.create_discord_entity(item_data_dict)
                        created_count += 1
                        processed_entities_responses.append(DiscordEntityDTO.model_validate(new_entity.__dict__).model_dump())
                    except Exception as e:
                        errors.append({"name": item_command.name, "error": f"Ошибка создания: {e}"})
                        self.logger.warning(f"Ошибка создания сущности {item_command.name}: {e}")

            self.logger.info(f"Синхронизация для гильдии {guild_id} завершена. Создано: {created_count}, Обновлено: {updated_count}. (Correlation ID: {command_dto.correlation_id})")

            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Синхронизация завершена. Создано: {created_count}, Обновлено: {updated_count}.",
                data={
                    "created_count": created_count,
                    "updated_count": updated_count,
                    "errors": errors,
                    "processed_entities": processed_entities_responses
                },
                client_id=command_dto.client_id # <-- Здесь client_id передается
            )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при синхронизации сущностей для гильдии {guild_id} (Correlation ID: {command_dto.correlation_id}): {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data={
                    "created_count": 0,
                    "updated_count": 0,
                    "errors": [{"error": f"Критическая ошибка на сервере: {e}"}],
                    "processed_entities": []
                },
                client_id=command_dto.client_id # <-- И здесь client_id передается
            )
