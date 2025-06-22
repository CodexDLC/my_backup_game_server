import discord # <--- Изменено
from discord.ext import commands # <--- Изменено
from Discord_API.config.logging.logging_setup_discod import logger # Используем ваш логгер

async def load_events(bot: commands.Bot):
    """Загружает все события (ивенты) как расширения."""
    events = [
        "Discord_API.events.discord_events.guild_welcome",
        "Discord_API.events.discord_events.regestration",
    ]

    for event_module in events:
        try:
            await bot.load_extension(event_module)
            logger.info(f"✅ Загружено событие: {event_module}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки события {event_module}: {e}")
