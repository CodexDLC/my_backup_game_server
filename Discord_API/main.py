# Discord_API/main.py
import sys
import asyncio
from dotenv import load_dotenv

# 1. Загрузка окружения ПЕРВОЙ операцией
load_dotenv()

# 2. Пути импорта
sys.path.append("/app")
print(f"🔎 PYTHONPATH: {sys.path}")

# 3. Импорт библиотек и ваших модулей
import discord
from discord.ext import commands
from Discord_API.discord_settings import BOT_PREFIX, DISCORD_TOKEN
from Discord_API.config.logging.logging_setup_discod import logger
from Discord_API.cog_manager import CommandsManager
from Discord_API.event_manager import load_events

# --- ДОБАВЛЕНО: Импорт вашего BotCommandClient ---
from Discord_API.command_client import BotCommandClient
# --- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ---

class Bot(commands.Bot):
    def __init__(self):
        # Определение намерений (Intents)
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        logger.info(f"Бот инициализирован с префиксом: {BOT_PREFIX}")

        # --- ДОБАВЛЕНО: Хранение экземпляра BotCommandClient ---
        self.command_client: BotCommandClient = None 
        # --- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ---

    async def setup_hook(self):
        """
        Вызывается при запуске для асинхронной инициализации.
        """
        logger.info("--- Запуск setup_hook ---")
        
        # 1. Загрузка событий через ваш event_manager
        logger.info("Загрузка событий...")
        await load_events(self)
        
        # 2. Загрузка когов через ваш cog_manager
        logger.info("Загрузка когов...")
        cog_manager = CommandsManager(self, base_dir="Discord_API/cogs")
        await cog_manager.load_cogs()

        # --- ДОБАВЛЕНО: Инициализация и запуск BotCommandClient ---
        logger.info("Инициализация и запуск BotCommandClient...")
        try:
            self.command_client = BotCommandClient(self) # Передаем экземпляр бота
            # Запускаем метод listen_for_commands как фоновую асинхронную задачу
            asyncio.create_task(self.command_client.listen_for_commands())
            logger.info("⚡ BotCommandClient успешно запущен как фоновая задача.")
        except ValueError as ve:
            logger.critical(f"❌ Ошибка конфигурации BotCommandClient: {ve}. Бот не будет функционировать корректно без подключения к шлюзу.", exc_info=True)
            # Возможно, здесь стоит выйти из приложения или продолжить, но с предупреждением
        except Exception as e:
            logger.critical(f"💥 Критическая ошибка при инициализации BotCommandClient: {e}", exc_info=True)
            # Аналогично, обработка ошибки инициализации
        # --- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ---

    async def on_ready(self):
        """Вызывается, когда бот успешно подключился."""
        logger.info(f"🟢 Бот {self.user} успешно запущен и готов к работе!")
        await self.change_presence(activity=discord.Game(name=f"Используйте {BOT_PREFIX}help"))


async def main():
    """Главная асинхронная функция для запуска бота."""
    bot = Bot()
    try:
        logger.info("🚀 Запуск бота...")
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.critical("🔑 Неверный токен Discord! Проверьте переменную DISCORD_TOKEN.")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске бота: {e}", exc_info=True)
    finally:
        # --- ДОБАВЛЕНО: Корректное завершение BotCommandClient ---
        if bot.command_client:
            logger.info("Остановка BotCommandClient...")
            await bot.command_client.stop() # Предполагается наличие метода stop() для закрытия WS
        # --- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ---

        if bot and not bot.is_closed():
            await bot.close()
        logger.info("🔚 Работа бота завершена.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную.")