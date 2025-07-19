# app/services/authentication/authentication_service.py
import discord
import inject
from discord.ext import commands


from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.config.discord_settings import HUB_GUILD_ID, REGISTRATION_CHANNEL_ID
from game_server.config.logging.logging_setup import app_logger as logger

# 👇 ИМПОРТЫ НОВЫХ ФЛОУ
from ..flows.hub_registration_flow import execute_hub_registration_flow
from ..flows.shard_login_flow import execute_shard_login_flow

# Импорты всех необходимых зависимостей
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager
from game_server.app_discord_bot.app.services.utils.player_login_intent_processor import PlayerLoginIntentProcessor
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper


class AuthenticationService:
    """
    Сервис-оркестратор, отвечающий за запуск процессов регистрации и аутентификации.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        account_data_manager: IAccountDataManager,
        role_finder: RoleFinder,
        base_ops: BaseDiscordOperations,
        guild_config_manager: IGuildConfigManager,
        player_login_processor: PlayerLoginIntentProcessor,
        request_helper: RequestHelper
    ):
        self.bot = bot
        self.account_data_manager = account_data_manager
        self.base_ops = base_ops
        self.guild_config_manager = guild_config_manager
        self.player_login_processor = player_login_processor
        self.request_helper = request_helper
        self.role_finder = role_finder


    async def start_hub_registration(self, interaction: discord.Interaction) -> None:
        if interaction.guild.id != HUB_GUILD_ID:
            await interaction.response.send_message("Эту команду можно использовать только на главном сервере (Хабе).", ephemeral=True)
            return
        if interaction.channel.id != REGISTRATION_CHANNEL_ID:
            await interaction.response.send_message(f"Пожалуйста, используйте эту команду в канале <#{REGISTRATION_CHANNEL_ID}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await execute_hub_registration_flow(
                interaction=interaction,
                bot=self.bot,
                account_data_manager=self.account_data_manager,
                base_ops=self.base_ops,
                guild_config_manager=self.guild_config_manager,
                request_helper=self.request_helper
            )
        except Exception as e:
            logger.critical(f"Критический сбой в execute_hub_registration_flow: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.followup.send("❌ Произошла непредвиденная системная ошибка. Сообщение передано разработчикам.")


    async def start_shard_login(self, interaction: discord.Interaction):
        """Запускает процесс логина на игровом шарде."""
        logger.info(f"Пользователь {interaction.user.id} инициировал логин на шарде {interaction.guild.id}.")
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        can_login = await self.player_login_processor.process_login_intent(interaction)
        if not can_login:
            logger.warning(f"Процесс логина для {interaction.user.id} был прерван процессором pre-login.")
            return
            
        # ▼▼▼ ИЗМЕНЕНИЕ: Передаем role_finder в флоу ▼▼▼
        await execute_shard_login_flow(
            interaction=interaction,
            bot=self.bot,
            account_data_manager=self.account_data_manager,
            base_ops=self.base_ops,
            role_finder=self.role_finder
        )
