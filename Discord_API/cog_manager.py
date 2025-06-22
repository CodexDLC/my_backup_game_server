import os
import discord # <--- Изменено
from discord.ext import commands # <--- Изменено
from Discord_API.config.logging.logging_setup_discod import logger

class CommandsManager: # Убрано наследование от Cog, так как это не требуется
    def __init__(self, bot: commands.Bot, base_dir="Discord_API/cogs"):
        self.bot = bot
        self.base_dir = os.path.abspath(base_dir)
        
        self.EXCLUDED_DIRS = {"__pycache__", "blueprints", "interface_templates", "utils"}
        self.EXCLUDED_FILES = {"__init__.py", "setup_world.txt", "channels_config.json"}
        self.EXCLUDED_PREFIXES = ("_",)
        
        self.loaded_cogs = set()
        logger.info(f"🚀 Менеджер когов | Базовый путь: {self.base_dir}")

    def _is_valid_cog(self, path: str) -> bool:
        filename = os.path.basename(path)
        dirname = os.path.basename(os.path.dirname(path))
        if filename in self.EXCLUDED_FILES or filename.startswith(self.EXCLUDED_PREFIXES) or dirname in self.EXCLUDED_DIRS:
            return False
        return filename.endswith(".py")

    def _path_to_module(self, path: str) -> str:
        # Конвертирует путь вида /app/Discord_API/cogs/admin/cmd.py 
        # в формат Discord_API.cogs.admin.cmd
        rel_path = os.path.relpath(path, start=os.path.join(self.base_dir, "..", ".."))
        return rel_path.replace(".py", "").replace(os.sep, ".")

    async def load_cogs(self) -> bool:
        if not os.path.exists(self.base_dir):
            logger.error(f"❌ Папка когов не найдена: {self.base_dir}")
            return False

        logger.info(f"🔍 Сканирование когов в: {self.base_dir}")
        success_count = 0
        total_files = 0

        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            for filename in files:
                file_path = os.path.join(root, filename)
                total_files += 1
                if self._is_valid_cog(file_path):
                    module_name = self._path_to_module(file_path)
                    logger.debug(f"⚙️ Найден ког: {module_name}")
                    if await self._load_cog(module_name):
                        success_count += 1
                else:
                    logger.debug(f"⏩ Пропущен: {filename}")

        logger.info(f"✅ Загружено когов: {success_count} из {total_files} файлов")
        return success_count > 0

    async def _load_cog(self, module_name: str) -> bool:
        try:
            await self.bot.load_extension(module_name)
            self.loaded_cogs.add(module_name)
            logger.success(f"⬆️ Загружен: {module_name}") # Используем logger.success для наглядности
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кога {module_name}", exc_info=True)
            return False

    # Функции перезагрузки когов остаются такими же, как у вас
    async def reload_cogs(self):
        for cog in self.loaded_cogs:
            try:
                await self.bot.reload_extension(cog)
                logger.success(f"🔄 Перезагружен: {cog}")
            except Exception as e:
                logger.error(f"❌ Ошибка перезагрузки кога {cog}", exc_info=True)

# Функция setup для загрузки этого кога CommandsManager
async def setup(bot: commands.Bot): # <-- 🔥🔥🔥 ИСПРАВЛЕНИЕ ЗДЕСЬ: ЯВНАЯ ТИПИЗАЦИЯ bot 🔥🔥🔥
    """
    Функция setup для загрузки этого кога (CommandsManager) в бота.
    """
    manager_cog = CommandsManager(bot)
    bot.add_cog(manager_cog) # Добавляем CommandsManager как ког
    
    logger.info("CommandsManager Cog загружен. Начинаем синхронную загрузку остальных когов...")
    # 🔥🔥🔥 ИЗМЕНЕНО: теперь setup_hook в main.py вызывает manager_cog.load_cogs() напрямую.
    # Так что здесь мы просто логируем, что ког-менеджер загружен.
    # Реальная загрузка других когов будет инициирована из main.py.
    # УДАЛИТЕ ЭТУ СТРОКУ, если вы хотите, чтобы загрузка когов ждала в setup_hook в main.py
    # await manager_cog.load_cogs() # <--- Если вы хотите, чтобы setup этого кога блокировал загрузку, добавьте await
    # Но согласно нашей стратегии, это делает setup_hook в main.py