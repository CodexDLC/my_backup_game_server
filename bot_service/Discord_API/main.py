#!/usr/bin/env python3
import os
import sys

import asyncio
import game_server.logger.logger_config as logger
from dotenv import load_dotenv
import discord
from discord.ext import commands



# Настройка логирования


# Загрузка переменных окружения
root_env = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '.env')
)
load_dotenv(root_env)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Настройка путей
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импорты после настройки путей
from commands import setup
from utils.update_inits import update_all_init_files

# Кастомный класс бота
class Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)
        # Здесь можно будет добавить подключение к базе данных позже, если нужно

    async def setup_hook(self) -> None:
        """Асинхронная инициализация бота."""
        try:
            print("🚀 setup(bot) вызывается")
            await setup(self)  # Загружаем все коги            
            logger.info("INFO Коги успешно загружены")
        except Exception as e:
            logger.error(f"ERROR Ошибка при загрузке когов: {e}")
            raise

    async def on_ready(self) -> None:
        logger.info(f"INFO Бот запущен как {self.user} (ID: {self.user.id})")

        from cogs.interface_templates.Admin_components import AdminPanelView
        from events.discord_events.admin_panel_event import send_or_update_admin_panel

        self.add_view(AdminPanelView(self))  # ← сохраняем активную панель
        await send_or_update_admin_panel(self)  # ← отправляем/обновляем панель, если надо



    async def on_message(self, message):
        """Обрабатываем сообщения."""
        if message.author == self.user:
            return
        await self.process_commands(message)

# Обновление __init__.py файлов
def update_discord_imports():
    """Обновляет __init__.py в папке Discord_API."""
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    directory = os.path.join(base_dir, "bot-service", "Discord_API")
    update_all_init_files(directory)
    logger.info(f"INFO Импорты обновлены: {directory}")

# Главная функция запуска бота
async def main():
    logger.info("🚀 Инициализация бота начата...")
    update_discord_imports()
    bot = Bot()
    try:
        logger.info("🚀 Запуск бота...")
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен вручную")
    except Exception as e:
        logger.error(f"INFO Критическая ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запускаем main()")
    asyncio.run(main())
