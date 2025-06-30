import discord # <--- Изменено
from discord.ext import commands # <--- Изменено
from game_server.config.logging.logging_setup import app_logger as logger

async def load_events(bot: commands.Bot):
    """Загружает все события (ивенты) как расширения."""
    events = [

    ]

    for event_module in events:
        try:
            await bot.load_extension(event_module)
            logger.info(f"✅ Загружено событие: {event_module}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки события {event_module}: {e}")
