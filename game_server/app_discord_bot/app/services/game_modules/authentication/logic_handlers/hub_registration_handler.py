import discord
import inject
import logging
from discord.ext import commands

from game_server.app_discord_bot.app.services.core_services.admin.base_discord_operations import BaseDiscordOperations

# Импортируем вашу основную функцию
from ..flows.hub_registration_flow import execute_hub_registration_flow

# Импортируем все зависимости
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager

from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
# --- ИЗМЕНЕНИЕ: Заменяем RequestHelper на WebSocketManager ---
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

class HubRegistrationFlowHandler:
    """
    Класс-адаптер, который вызывает execute_hub_registration_flow,
    используя WebSocket для связи.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        account_data_manager: AccountDataManager,
        base_ops: BaseDiscordOperations,
        guild_config_manager: GuildConfigManager,
        ws_manager: WebSocketManager, # <-- ЗАПРАШИВАЕМ WebSocketManager
        logger: logging.Logger
    ):
        self.bot = bot
        self.account_data_manager = account_data_manager
        self.base_ops = base_ops
        self.guild_config_manager = guild_config_manager
        self.ws_manager = ws_manager # <-- СОХРАНЯЕМ WebSocketManager
        self.logger = logger

    async def execute(self, payload: str | None, interaction: discord.Interaction, **kwargs) -> None:
        self.logger.info("HubRegistrationFlowHandler: Запуск execute...")
        await execute_hub_registration_flow(
            interaction=interaction,
            # bot=self.bot, # Удаляем передачу bot
            account_data_manager=self.account_data_manager,
            base_ops=self.base_ops,
            guild_config_manager=self.guild_config_manager,
            ws_manager=self.ws_manager
        )
        
        self.logger.info("HubRegistrationFlowHandler: Работа завершена, возвращаем None.")
        return None