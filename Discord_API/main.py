#!/usr/bin/env python3
import os
import asyncio
import sys

from Discord_API.discord_settings import BOT_PREFIX, DISCORD_TOKEN
from Discord_API.event_manager import load_events


sys.path.append("/app/Discord_API") 
print(f"🔎 PYTHONPATH: {sys.path}")
from dotenv import load_dotenv
import discord
from discord.ext import commands
from Discord_API.config.logging.logging_setup import logger
from Discord_API.cog_manager import setup

load_dotenv()




if not DISCORD_TOKEN:
    raise ValueError("Токен Discord не найден!")


class Bot(commands.Bot):
    def __init__(self):
        # ИЛИ точная настройка:
        intents = discord.Intents.default()
        intents.members = True       # Для отслеживания участников
        intents.invites = True       # Для работы с инвайтами
        intents.message_content = True
        intents.guilds = True
        intents.presences = True     # Если нужно отслеживать статусы
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)

    async def setup_hook(self):
        await setup(self)    # 🔥 Передаём бота в менеджер когов напрямую
        await load_events(self)    # Загружаем события
        
    async def on_ready(self):
        logger.info(f"Бот запущен как {self.user}")
        await self.change_presence(activity=discord.Game(name="Type !help"))

    async def on_message(self, message):
        if message.author == self.user:
            return
        try:
            await self.process_commands(message)
        except Exception as e:
            logger.error(f"Ошибка в команде: {e}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Команда не найдена!")
        else:
            logger.error(f"Ошибка: {error}")



async def main():
    bot = Bot()
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
