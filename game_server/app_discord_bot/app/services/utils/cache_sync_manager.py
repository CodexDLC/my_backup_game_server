# game_server/app_discord_bot/app/services/utils/cache_sync_manager.py

import inject
import logging
from discord.ext import commands
from typing import Optional # Импортируем Optional

from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.contracts.api_models.discord.config_management_requests import GuildConfigDeleteRequest, GuildConfigSyncRequest


class CacheSyncManager:
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        request_helper: RequestHelper,
        guild_config_manager: GuildConfigManager,
        logger: logging.Logger
    ):
        self.bot = bot
        self.logger = logger
        self.request_helper: RequestHelper = request_helper
        self.guild_config_manager: GuildConfigManager = guild_config_manager
        self.logger.info("✨ CacheSyncManager инициализирован.")

    async def sync_guild_config_to_backend(self, guild_id: int, shard_type: str) -> bool: # Добавляем shard_type
        """
        Синхронизирует полную конфигурацию гильдии из локального кэша Redis с бэкендом.
        :param guild_id: ID гильдии Discord.
        :param shard_type: Тип шарда (например, "hub" или "game"), для которого синхронизируется конфигурация.
        :return: True, если синхронизация успешна, False в противном случае.
        """
        self.logger.info(f"Запущена синхронизация конфигурации из кэша в бэкенд для гильдии {guild_id} (тип шарда: {shard_type})...")
        
        # Передаем shard_type в get_all_fields
        config_data = await self.guild_config_manager.get_all_fields(guild_id, shard_type) 

        if not config_data:
            self.logger.warning(f"Локальный кэш для гильдии {guild_id} (тип шарда: {shard_type}) пуст. Синхронизация отменена.")
            return True 

        try:
            payload = GuildConfigSyncRequest(
                guild_id=guild_id,
                config_data=config_data,
                client_id=self.request_helper.client_id
            )
            
            response, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_config_from_bot,
                request_payload=payload,
                correlation_id=payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "cache_to_backend_sync", "shard_type": shard_type} # Добавляем shard_type в контекст
            )

            if response and response.get('payload', {}).get('status') == 'success':
                self.logger.success(f"Конфигурация гильдии {guild_id} (тип шарда: {shard_type}) успешно синхронизирована с бэкендом.")
                return True
            else:
                # УЛУЧШЕННОЕ ЛОГИРОВАНИЕ: записываем весь ответ, чтобы видеть его полную структуру
                self.logger.error(
                    f"Бэкенд вернул неуспешный ответ при синхронизации конфигурации гильдии {guild_id} (тип шарда: {shard_type}). "
                    f"Полный ответ от сервера: {response}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Критическая ошибка при синхронизации конфигурации гильдии {guild_id} (тип шарда: {shard_type}) с бэкендом: {e}", exc_info=True)
            return False

    async def delete_guild_config_from_backend(self, guild_id: int, shard_type: str) -> bool: # Добавляем shard_type
        """
        Отправляет команду на удаление конфигурации гильдии из бэкенд-Redis.
        :param guild_id: ID гильдии Discord.
        :param shard_type: Тип шарда (например, "hub" или "game"), для которого удаляется конфигурация.
        :return: True, если удаление успешно, False в противном случае.
        """
        self.logger.info(f"Запущена команда на удаление конфигурации гильдии {guild_id} (тип шарда: {shard_type}) из бэкенд-Redis...")
        try:
            payload = GuildConfigDeleteRequest(
                guild_id=guild_id,
                client_id=self.request_helper.client_id
            )
            
            response, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.delete_config_from_bot,
                request_payload=payload,
                correlation_id=payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "cache_to_backend_delete", "shard_type": shard_type} # Добавляем shard_type в контекст
            )

            if response and response.get("status") == "success":
                self.logger.success(f"Конфигурация гильдии {guild_id} (тип шарда: {shard_type}) успешно удалена из бэкенд-Redis.")
                return True
            else:
                error_msg = response.get('message') if response else "Нет ответа от сервера"
                self.logger.error(f"Бэкенд вернул ошибку при удалении конфигурации гильдии {guild_id} (тип шарда: {shard_type}) из Redis: {error_msg}")
                return False
        except Exception as e:
            self.logger.error(f"Критическая ошибка при удалении конфигурации гильдии {guild_id} (тип шарда: {shard_type}) из бэкенд-Redis: {e}", exc_info=True)
            return False
