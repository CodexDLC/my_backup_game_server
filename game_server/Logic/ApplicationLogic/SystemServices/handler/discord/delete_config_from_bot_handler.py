# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/delete_config_from_bot_handler.py

import logging
from typing import Dict, Any

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_cache.services.discord.backend_guild_config_manager import BackendGuildConfigManager
from game_server.common_contracts.api_models.discord_api import GuildConfigDeleteRequest
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO


class DeleteConfigFromBotHandler(ISystemServiceHandler):
    """
    Обработчик для удаления полной конфигурации гильдии из кэша Redis на стороне бэкенда.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            # Ожидаем, что в зависимости будет передан менеджер кэша для бэкенда
            self.cache_manager: BackendGuildConfigManager = self.dependencies['guild_config_manager']
        except KeyError:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость 'guild_config_manager'.")
            raise

    async def process(self, command_dto: GuildConfigDeleteRequest) -> BaseResultDTO[Dict[str, Any]]:
        guild_id = command_dto.guild_id
        
        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Начинаем удаление конфигурации из кэша бэкенда. (Correlation ID: {command_dto.correlation_id})")

        try:
            # Вызываем метод менеджера кэша для удаления всей конфигурации гильдии
            await self.cache_manager.delete_config(guild_id)
            
            self.logger.success(f"Конфигурация для гильдии {guild_id} успешно удалена из кэша бэкенда.")
            
            # Возвращаем успешный результат
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Конфигурация для гильдии {guild_id} успешно удалена.",
                data={"guild_id": guild_id}, # Можно вернуть ID удаленной гильдии
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при удалении конфигурации из кэша для гильдии {guild_id}: {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Критическая ошибка на сервере при удалении конфигурации: {e}",
                data={"guild_id": guild_id, "error": str(e)},
                client_id=command_dto.client_id
            )

