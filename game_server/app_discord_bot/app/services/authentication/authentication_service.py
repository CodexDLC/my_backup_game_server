# app/services/authentication/authentication_service.py
import discord
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.app.constant.constants_world import HUB_GUILD_ID, REGISTRATION_CHANNEL_ID

# Импортируем наш новый файл с логикой
from .flows.hub_registration_flow import execute_hub_registration_flow

class AuthenticationService:
    """
    Сервис-оркестратор, отвечающий за запуск процессов регистрации и аутентификации.
    """
    def __init__(self, bot):
        self.bot = bot
        # Здесь больше не нужен self.base_ops, так как он используется внутри flow

    async def start_hub_registration(self, interaction: discord.Interaction) -> None:
        """
        Проверяет условия и запускает процесс регистрации на хабе.
        """
        # 1. Проверки остаются здесь, в "контроллере"
        if interaction.guild.id != HUB_GUILD_ID:
            await interaction.response.send_message("Эту команду можно использовать только на главном сервере (Хабе).", ephemeral=True)
            return
        if interaction.channel.id != REGISTRATION_CHANNEL_ID:
            await interaction.response.send_message(f"Пожалуйста, используйте эту команду в канале <#{REGISTRATION_CHANNEL_ID}>.", ephemeral=True)
            return

        # 2. Отправляем первоначальный ответ и делегируем выполнение
        await interaction.response.send_message("Ваш запрос на регистрацию принят. Обрабатываю...", ephemeral=True)
        
        try:
            # Вызываем внешний, более сложный процесс
            await execute_hub_registration_flow(self.bot, interaction)
        except Exception as e:
            # Ловим самые общие ошибки на случай, если flow упадет до блока try-except
            logger.critical(f"Критический сбой в execute_hub_registration_flow: {e}", exc_info=True)
            await interaction.edit_original_response(content="❌ Произошла непредвиденная системная ошибка. Сообщение передано разработчикам.")


    async def start_shard_login(self, interaction: discord.Interaction):
        """
        ЗАГЛУШКА: Запускает процесс логина на игровом шарде.
        """
        logger.info(f"Пользователь {interaction.user.id} инициировал логин на шарде {interaction.guild.id}.")
        await interaction.response.send_message("Функционал логина находится в разработке...", ephemeral=True)
        # В будущем здесь будет вызов `execute_shard_login_flow(self.bot, interaction)`
