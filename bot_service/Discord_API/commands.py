import os
import logging

# Логгер для загрузки когов
logger = logging.getLogger("CommandsLoader")

class CommandsManager:
    def __init__(self, bot, cogs_directory="cogs"):
        """
        Инициализация менеджера когов.
        :param bot: экземпляр бота
        :param cogs_directory: папка с когами
        """
        self.bot = bot
        self.cogs_directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            cogs_directory
        )
        logger.info(f"Путь к папке cogs: {self.cogs_directory}")

    async def load_cogs(self):
        """
        Загружает все коги из указанной папки, пропуская исключённые директории.
        """
        EXCLUDED_FOLDERS = ["blueprints","interface_templates"]  # Исключаем папку blueprints        

        if not os.path.exists(self.cogs_directory):
            logger.error(f"Папка {self.cogs_directory} не найдена!")
            return

        for root, dirs, files in os.walk(self.cogs_directory):
            # Убираем исключённые папки прямо на месте
            dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS]

            for filename in files:
                if filename.endswith(".py") and filename != "__init__.py":
                    relative_path = os.path.relpath(root, self.cogs_directory).replace(os.sep, ".")
                    cog_name = f"cogs.{relative_path}.{filename[:-3]}" if relative_path != "." else f"cogs.{filename[:-3]}"
                    logger.info(f"Попытка загрузки ког: {cog_name}")

                    try:
                        await self.bot.load_extension(cog_name)
                        logger.info(f"INFO Загружен ког: {cog_name}")
                    except Exception as e:
                        logger.error(f"ERROR Ошибка загрузки кога {cog_name}: {e}")

# Внешняя точка входа для Discord бота
async def setup(bot):
    manager = CommandsManager(bot)
    await manager.load_cogs()
