# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/sync_config_from_bot_handler.py
# Version: 0.001

import logging # ▼▼▼ НОВЫЙ ИМПОРТ: logging ▼▼▼
from typing import Dict, Any
import inject # ▼▼▼ НОВЫЙ ИМПОРТ: inject ▼▼▼

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_cache.services.discord.backend_guild_config_manager import BackendGuildConfigManager
from game_server.contracts.api_models.discord.config_management_requests import GuildConfigSyncRequest
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO

class SyncConfigFromBotHandler(ISystemServiceHandler):
    """
    Обработчик для сохранения полной конфигурации шарда, полученной от Discord-бота,
    в кэш Redis на стороне бэкенда.
    """
    # ▼▼▼ ИСПОЛЬЗУЕМ @inject.autoparams() И ЯВНО ОБЪЯВЛЯЕМ ЗАВИСИМОСТИ ▼▼▼
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, guild_config_manager: BackendGuildConfigManager):
        self._logger = logger
        self.cache_manager: BackendGuildConfigManager = guild_config_manager # Переименовал для ясности
        self._logger.info("SyncConfigFromBotHandler инициализирован.")

    # ▼▼▼ РЕАЛИЗАЦИЯ АБСТРАКТНОГО СВОЙСТВА logger ИЗ ISystemServiceHandler ▼▼▼
    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, command_dto: GuildConfigSyncRequest) -> BaseResultDTO[Dict[str, Any]]:
        guild_id = command_dto.guild_id
        config_data = command_dto.config_data
        
        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Сохранение конфигурации в кэш бэкенда...")

        try:
            # Проходим по всем полям, полученным от бота, и сохраняем их в кэш бэкенда
            for field_name, data in config_data.items():
                await self.cache_manager.set_field(
                    guild_id=guild_id,
                    field_name=field_name,
                    data=data
                )
            
            self.logger.success(f"Конфигурация для гильдии {guild_id} успешно сохранена в кэш бэкенда.")
            
            # Возвращаем успешный результат
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Конфигурация для гильдии {guild_id} успешно принята и сохранена.",
                data={"fields_processed": len(config_data)},
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при сохранении конфигурации в кэш для гильдии {guild_id}: {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка на сервере при обработке конфигурации: {e}",
                data={"error": str(e), "guild_id": guild_id}, # ▼▼▼ ИСПОЛЬЗУЕМ Dict для data ▼▼▼
                client_id=command_dto.client_id
            )
