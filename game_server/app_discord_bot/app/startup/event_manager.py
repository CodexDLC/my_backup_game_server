# game_server/app_discord_bot/app/startup/event_manager.py
import discord
from discord.ext import commands
import logging
import inject

# 🔥 НОВОЕ: Импортируем наш новый обработчик
from game_server.app_discord_bot.app.events.player_events_handler import PlayerEventsHandler

class EventManager:
    """Регистрирует основные обработчики событий бота."""
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger, player_events_handler: PlayerEventsHandler):
        self.bot = bot
        self.logger = logger
        # 🔥 НОВОЕ: Сохраняем экземпляр обработчика
        self.player_events_handler = player_events_handler

    def register_events(self):
        """Регистрирует все необходимые события."""
        
        # 🔥🔥🔥 УДАЛИТЕ ИЛИ ЗАКОММЕНТИРУЙТЕ СЛЕДУЮЩИЙ БЛОК on_ready 🔥🔥🔥
        # @self.bot.event
        # async def on_ready():
        #     self.logger.info(f'✅ {self.bot.user} успешно подключился к Discord!')
        #     self.logger.info(f"ID бота: {self.bot.user.id}")

        # 🔥 НОВОЕ: Регистрируем обработчик для события on_member_join
        @self.bot.event
        async def on_member_join(member: discord.Member):
            # Просто вызываем метод из нашего чистого обработчика
            await self.player_events_handler.handle_player_join(member)

        self.logger.info("✅ Основные события Discord успешно зарегистрированы (кроме on_ready, которое теперь только в GameBot).")