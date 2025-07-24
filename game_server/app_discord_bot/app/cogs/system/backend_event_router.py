# game_server/app_discord_bot/app/cogs/system/backend_event_router.py
import inject
import discord
import logging
from discord.ext import commands
from unittest.mock import MagicMock

class BackendEventRouter(commands.Cog):
    """
    Слушает внутренние события от бэкенда, имитирует объект Interaction
    и передает его в главный InteractionRouter для обработки.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
        self.logger.info("[+] Слушатель внутренних событий от бэкенда активен.")

    @commands.Cog.listener('on_backend_event')
    async def on_backend_event(self, custom_id: str, data: dict):
        self.logger.info(f"Поймано внутреннее событие on_backend_event с custom_id: '{custom_id}'")

        # ✅ ИЩЕМ РОУТЕР ПРЯМО ЗДЕСЬ, "В ПОСЛЕДНИЙ МОМЕНТ"
        interaction_router = self.bot.get_cog("InteractionRouter")

        if not interaction_router:
            self.logger.error("Не удалось найти InteractionRouter для передачи управления.")
            return

        # Создаем "фальшивую" интеракцию.
        # Она не сможет отвечать в чат, но сможет передать custom_id.
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.data = {'custom_id': custom_id}
        # Добавляем "заглушки" для методов, которые может вызвать роутер,
        mock_interaction.is_background_event = True
        # чтобы избежать ошибок.
        mock_interaction.response = MagicMock()
        mock_interaction.response.is_done.return_value = True
        # Добавляем пустой user, чтобы не было ошибки, если роутер обратится к нему
        mock_interaction.user = MagicMock(spec=discord.User)

        # Вызываем главный роутер с нашей фальшивой интеракцией
        await interaction_router.main_interaction_router(mock_interaction)