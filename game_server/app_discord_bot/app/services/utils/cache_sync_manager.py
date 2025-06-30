# game_server/app_discord_bot/app/services/utils/cache_sync_manager.py
from typing import Dict, Any
import discord

from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
# Добавляем импорт GuildConfigDeleteRequest
from game_server.common_contracts.api_models.discord_api import GuildConfigSyncRequest, GuildConfigDeleteRequest
from game_server.config.logging.logging_setup import app_logger as logger


class CacheSyncManager:
    """
    Отправляет полную конфигурацию гильдии из кэша на бэкенд для сохранения копии.
    Теперь также отвечает за явное удаление конфигурации на бэкенде.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.logger = logger
        
        if not hasattr(bot, 'request_helper'):
            self.logger.critical("RequestHelper не инициализирован в объекте бота.")
            raise RuntimeError("RequestHelper не инициализирован в объекте бота.")
        self.request_helper: RequestHelper = bot.request_helper

        if not hasattr(bot, 'cache_manager') or not hasattr(bot.cache_manager, 'guild_config'):
            self.logger.critical("GuildConfigManager не инициализирован в объекте бота.")
            raise RuntimeError("GuildConfigManager не инициализирован в объекте бота.")
        self.guild_config_manager: GuildConfigManager = bot.cache_manager.guild_config

        self.logger.info("✨ CacheSyncManager инициализирован.")

    async def sync_guild_config_to_backend(self, guild_id: int) -> bool:
        """
        Считывает всю конфигурацию из локального кэша Redis для указанной гильдии
        и отправляет ее на бэкенд для синхронизации (создания/обновления).
        """
        self.logger.info(f"Запущена синхронизация конфигурации из кэша в бэкенд для гильдии {guild_id}...")

        config_data = await self.guild_config_manager.get_all_fields(guild_id)

        if not config_data:
            self.logger.warning(f"Локальный кэш для гильдии {guild_id} пуст. Синхронизация отменена.")
            # Если кэш пуст, это может означать, что конфигурация уже удалена локально.
            # В этом случае, мы можем явно отправить команду на удаление на бэкенд.
            # Однако, текущая логика sync_guild_config_to_backend предназначена для "pushing data".
            # Для удаления будет отдельный метод.
            return True 

        try:
            payload = GuildConfigSyncRequest(
                guild_id=guild_id,
                config_data=config_data,
                client_id=self.request_helper.bot_name_for_gateway
            )
            
            response, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_config_from_bot,
                request_payload=payload,
                correlation_id=payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "cache_to_backend_sync"}
            )

            if response and response.get("status") == "success":
                self.logger.success(f"Конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом.")
                return True
            else:
                error_msg = response.get('message') if response else "Нет ответа от сервера"
                self.logger.error(f"Бэкенд вернул ошибку при синхронизации конфигурации: {error_msg}")
                return False

        except Exception as e:
            self.logger.error(f"Критическая ошибка при синхронизации конфигурации гильдии {guild_id} с бэкендом: {e}", exc_info=True)
            return False

    async def delete_guild_config_from_backend(self, guild_id: int) -> bool:
        """
        Отправляет команду на бэкенд для явного удаления полной конфигурации гильдии из Redis.
        """
        self.logger.info(f"Запущена команда на удаление конфигурации гильдии {guild_id} из бэкенд-Redis...")
        try:
            payload = GuildConfigDeleteRequest(
                guild_id=guild_id,
                client_id=self.request_helper.bot_name_for_gateway
            )
            
            response, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.delete_config_from_bot, # НОВЫЙ API МЕТОД
                request_payload=payload,
                correlation_id=payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "cache_to_backend_delete"}
            )

            if response and response.get("status") == "success":
                self.logger.success(f"Конфигурация гильдии {guild_id} успешно удалена из бэкенд-Redis.")
                return True
            else:
                error_msg = response.get('message') if response else "Нет ответа от сервера"
                self.logger.error(f"Бэкенд вернул ошибку при удалении конфигурации из Redis: {error_msg}")
                return False
        except Exception as e:
            self.logger.error(f"Критическая ошибка при удалении конфигурации гильдии {guild_id} из бэкенд-Redis: {e}", exc_info=True)
            return False
