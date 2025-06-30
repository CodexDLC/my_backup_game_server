# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/delete_entities_handler.py

import logging
from typing import Dict, Any, List
from pydantic import ValidationError

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.common_contracts.api_models.discord_api import UnifiedEntityBatchDeleteRequest
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO


class DeleteDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для массового удаления сущностей Discord из БД.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.discord_entity_repo = self.repo_manager.discord_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    async def process(self, command_dto: UnifiedEntityBatchDeleteRequest) -> BaseResultDTO[Dict[str, Any]]:
        guild_id = command_dto.guild_id # Сохраняем guild_id, хотя он может не использоваться в репо
        discord_ids = command_dto.discord_ids
        
        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Начинаем массовое удаление {len(discord_ids)} сущностей. (Correlation ID: {command_dto.correlation_id})")

        deleted_count = 0
        try:
            # 1. Удаление сущностей из БД
            # ИСПРАВЛЕНИЕ: Передаем discord_id как позиционный аргумент,
            # так как метод не ожидает ключевого слова 'discord_id'.
            for discord_id in discord_ids:
                try:
                    success = await self.discord_entity_repo.delete_discord_entity_by_id(discord_id) # ИЗМЕНЕНО
                    if success:
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Ошибка при удалении сущности Discord ID {discord_id} для гильдии {guild_id}: {e}")
            
            self.logger.info(f"Успешно удалено {deleted_count} сущностей для гильдии {guild_id} из БД.")

            # 2. Возвращаем успешный результат
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Успешно удалено {deleted_count} сущностей для гильдии {guild_id}.",
                data={"deleted_count": deleted_count},
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при массовом удалении сущностей для гильдии {guild_id} (Correlation ID: {command_dto.correlation_id}): {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Критическая ошибка на сервере при массовом удалении: {e}",
                data={"deleted_count": 0, "error": str(e)},
                client_id=command_dto.client_id
            )
