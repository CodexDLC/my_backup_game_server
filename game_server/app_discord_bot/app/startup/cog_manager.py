# game_server/app_discord_bot/startup/commands_manager.py

import os
import discord
from discord.ext import commands
from game_server.config.logging.logging_setup import app_logger as logger

class CommandsManager:
    # bot: commands.Bot добавлен для ясности, как было у вас
    # base_dir_fs: Путь к директории на ФАЙЛОВОЙ СИСТЕМЕ, где лежат коги
    # base_dir_import: Путь для ИМПОРТА КОГОВ (Python-модуль)
    def __init__(self, bot: commands.Bot): # Удаляем base_dir из __init__, будем вычислять
        self.bot = bot
        
        # 🔥 ИСПРАВЛЕНИЕ 1: Определяем base_dir для ФАЙЛОВОЙ СИСТЕМЫ
        # __file__ это путь к текущему файлу commands_manager.py
        # os.path.dirname(__file__) -> game_server/app_discord_bot/startup/
        # os.path.join(..., "..", "app", "cogs") -> game_server/app_discord_bot/app/cogs
        self.base_dir_fs = os.path.join(os.path.dirname(__file__), "..", "cogs")
        self.base_dir_fs = os.path.abspath(self.base_dir_fs) # Убедимся, что это абсолютный путь
        
        # 🔥 ИСПРАВЛЕНИЕ 2: Определяем базовый путь для ИМПОРТА
        # Это должен быть Python-путь до папки 'cogs'
        # Начинается с корневого пакета вашего приложения в контейнере (game_server)
        self.base_import_prefix = "game_server.app_discord_bot.app.cogs"
        
        self.EXCLUDED_DIRS = {"__pycache__", "blueprints", "interface_templates", "utils"}
        self.EXCLUDED_FILES = {"__init__.py", "setup_world.txt", "channels_config.json"}
        self.EXCLUDED_PREFIXES = ("_",)
        
        self.loaded_cogs = set()
        logger.info(f"🚀 Менеджер когов | Базовый путь ФС: {self.base_dir_fs}")
        logger.info(f"🚀 Менеджер когов | Базовый путь импорта: {self.base_import_prefix}")

    def _is_valid_cog(self, path: str) -> bool:
        filename = os.path.basename(path)
        dirname = os.path.basename(os.path.dirname(path))
        if filename in self.EXCLUDED_FILES or filename.startswith(self.EXCLUDED_PREFIXES) or dirname in self.EXCLUDED_DIRS:
            return False
        return filename.endswith(".py")

    def _path_to_module(self, file_path_fs: str) -> str:
        # 🔥 ИСПРАВЛЕНИЕ 3: Вычисление Python-пути
        # file_path_fs: например, /app/game_server/app_discord_bot/app/cogs/admin/ui_cog.py
        # self.base_dir_fs: /app/game_server/app_discord_bot/app/cogs

        # Получаем относительный путь от base_dir_fs: admin/ui_cog.py
        rel_path_from_cogs = os.path.relpath(file_path_fs, start=self.base_dir_fs)
        
        # Преобразуем в Python-путь: admin.ui_cog
        module_path_suffix = rel_path_from_cogs.replace(".py", "").replace(os.sep, ".")
        
        # Объединяем с базовым импорт-префиксом: game_server.app_discord_bot.app.cogs.admin.ui_cog
        return f"{self.base_import_prefix}.{module_path_suffix}"

    async def load_cogs(self) -> bool:
        if not os.path.exists(self.base_dir_fs): # Используем base_dir_fs
            logger.error(f"❌ Папка когов не найдена: {self.base_dir_fs}")
            return False

        logger.info(f"🔍 Сканирование когов в: {self.base_dir_fs}")
        success_count = 0
        total_files = 0

        for root, dirs, files in os.walk(self.base_dir_fs): # Используем base_dir_fs
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            for filename in files:
                file_path_fs = os.path.join(root, filename) # Полный файловый путь
                total_files += 1
                if self._is_valid_cog(file_path_fs):
                    module_name = self._path_to_module(file_path_fs) # Передаем полный файловый путь
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
            logger.success(f"⬆️ Загружен: {module_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кога {module_name}", exc_info=True)
            return False

    async def reload_cogs(self):
        for cog in self.loaded_cogs:
            try:
                await self.bot.reload_extension(cog)
                logger.success(f"🔄 Перезагружен: {cog}")
            except Exception as e:
                logger.error(f"❌ Ошибка перезагрузки кога {cog}", exc_info=True)

# Функция setup для загрузки этого кога CommandsManager
async def setup(bot: commands.Bot):
    manager_cog = CommandsManager(bot)
    # bot.add_cog(manager_cog) # Обычно CommandsManager не является самим когом, а управляет ими.
                              # Если CommandsManager не является Cog, эту строку нужно убрать.
                              # Если CommandsManager должен быть когом, он должен наследоваться от commands.Cog
    await manager_cog.load_cogs() # Запускаем загрузку когов через менеджер

    logger.info("CommandsManager загружен и коги запущены.")