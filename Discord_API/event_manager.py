



import discord
from discord.ext import commands

async def load_events(bot):
    """Загружает все события (ивенты)"""
    events = [
        "Discord_API.events.discord_events.guild_welcome",  # ✅ Приветствие новых участников (если есть)
        "Discord_API.events.discord_events.regestration",  # 
        
    ]

    for event in events:
        try:
            await bot.load_extension(event)
            print(f"✅ Загружено событие: {event}")
        except Exception as e:
            print(f"❌ Ошибка загрузки {event}: {e}")
