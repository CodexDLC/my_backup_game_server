# game_server/app_discord_bot/app/startup/cog_manager.py

import os
import importlib.util
import inspect
import discord
from discord.ext import commands
from game_server.config.logging.logging_setup import app_logger as logger
import inject

# Для Prometheus: Определения метрик (примеры)
# from prometheus_client import Counter, Gauge # <--- Не забудьте установить prometheus_client

# COGS_LOAD_ATTEMPTS = Counter('discord_cogs_load_attempts_total', 'Total attempts to load Discord cogs.')
# COGS_LOAD_SUCCESS = Counter('discord_cogs_load_success_total', 'Total successful Discord cogs loaded.')
# COGS_LOAD_FAILURES = Counter('discord_cogs_load_failures_total', 'Total failed Discord cogs loads.', ['reason'])
# COGS_LOADED_COUNT = Gauge('discord_cogs_loaded_current', 'Current number of loaded Discord cogs.')
# COGS_RELOAD_ATTEMPTS = Counter('discord_cogs_reload_attempts_total', 'Total attempts to reload Discord cogs.')
# COGS_RELOAD_SUCCESS = Counter('discord_cogs_reload_success_total', 'Total successful Discord cogs reloads.')
# COGS_RELOAD_FAILURES = Counter('discord_cogs_reload_failures_total', 'Total failed Discord cogs reloads.')


class CommandsManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        self.base_dir_fs = os.path.join(os.path.dirname(__file__), "..", "cogs")
        self.base_dir_fs = os.path.abspath(self.base_dir_fs)
        
        self.base_import_prefix = "game_server.app_discord_bot.app.cogs"
        
        self.EXCLUDED_DIRS = {"__pycache__", "blueprints", "interface_templates", "utils"}
        self.EXCLUDED_FILES = {"__init__.py", "setup_world.txt", "channels_config.json"}
        self.EXCLUDED_PREFIXES = ("_",)
        
        self.loaded_cogs = set()
        logger.info(f"🚀 Менеджер когов | Базовый путь ФС: {self.base_dir_fs}")
        logger.info(f"🚀 Менеджер когов | Базовый путь импорта: {self.base_import_prefix}")
        logger.debug("DEBUG: CommandsManager инициализирован.")

    def _is_valid_cog(self, path: str) -> bool:
        filename = os.path.basename(path)
        dirname = os.path.basename(os.path.dirname(path))
        is_excluded = filename in self.EXCLUDED_FILES or \
                      filename.startswith(self.EXCLUDED_PREFIXES) or \
                      dirname in self.EXCLUDED_DIRS
        logger.debug(f"DEBUG: Проверка валидности кога '{filename}'. Исключен: {is_excluded}, Python файл: {filename.endswith('.py')}")
        return filename.endswith(".py") and not is_excluded

    def _path_to_module(self, file_path_fs: str) -> str:
        rel_path_from_cogs = os.path.relpath(file_path_fs, start=self.base_dir_fs)
        module_path_suffix = rel_path_from_cogs.replace(".py", "").replace(os.sep, ".")
        full_module_name = f"{self.base_import_prefix}.{module_path_suffix}"
        logger.debug(f"DEBUG: Преобразование пути '{file_path_fs}' в модуль '{full_module_name}'.")
        return full_module_name

    async def load_cogs(self) -> bool:
        logger.debug("DEBUG: Начинается процесс загрузки когов.")
        # COGS_LOAD_ATTEMPTS.inc() # Prometheus: инкремент попыток загрузки
        if not os.path.exists(self.base_dir_fs):
            logger.error(f"❌ Папка когов не найдена: {self.base_dir_fs}")
            # COGS_LOAD_FAILURES.labels(reason='folder_not_found').inc() # Prometheus
            return False

        logger.info(f"🔍 Сканирование когов в: {self.base_dir_fs}")
        success_count = 0
        total_files = 0

        for root, dirs, files in os.walk(self.base_dir_fs):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            logger.debug(f"DEBUG: Сканирование директории: {root}. Включенные поддиректории: {dirs}")
            for filename in files:
                file_path_fs = os.path.join(root, filename)
                total_files += 1
                if self._is_valid_cog(file_path_fs):
                    module_name = self._path_to_module(file_path_fs)
                    logger.debug(f"⚙️ Найден валидный файл кога: {module_name}")
                    if await self._load_cog(module_name):
                        success_count += 1
                else:
                    logger.debug(f"⏩ Пропущен невалидный файл: {filename}")

        logger.info(f"✅ Загружено когов: {success_count} из {total_files} файлов")
        # if success_count > 0:
            # COGS_LOAD_SUCCESS.inc(success_count) # Prometheus
            # COGS_LOADED_COUNT.set(len(self.loaded_cogs)) # Prometheus
        # else:
            # COGS_LOAD_FAILURES.labels(reason='no_cogs_loaded').inc() # Prometheus
        return success_count > 0

    async def _load_cog(self, module_name: str) -> bool:
        logger.debug(f"DEBUG: Попытка загрузки кога: {module_name}")
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                logger.error(f"❌ Не удалось найти спецификацию для модуля кога: {module_name}")
                # COGS_LOAD_FAILURES.labels(reason='spec_not_found').inc() # Prometheus
                return False
            
            lib = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lib)
            logger.debug(f"DEBUG: Модуль {module_name} успешно импортирован.")

            cog_class = None
            for name, obj in inspect.getmembers(lib):
                if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj != commands.Cog:
                    cog_class = obj
                    logger.debug(f"DEBUG: Найден класс кога '{cog_class.__name__}' в модуле '{module_name}'.")
                    break

            if cog_class is None:
                logger.error(f"❌ В модуле '{module_name}' не найден класс, наследующий от commands.Cog.")
                # COGS_LOAD_FAILURES.labels(reason='no_cog_class_found').inc() # Prometheus
                return False
            
            logger.debug(f"DEBUG: Попытка создать экземпляр кога {cog_class.__name__} через inject.instance().")
            
            # --- НАЧАЛО БЛОКА ОТЛАДКИ INJECTOR ---
            try:
                injector = inject.get_injector()
                if injector and hasattr(injector, '_bindings'):
                    logger.debug("DEBUG: Инжектор найден. Зарегистрированные привязки:")
                    for key, binding in injector._bindings.items():
                        provider_info = "Неизвестный провайдер"
                        if hasattr(binding, 'provider'):
                            provider_info = f"Провайдер: {binding.provider}"
                        elif hasattr(binding, 'value'): # Для прямых привязок значений
                            provider_info = f"Значение: {binding.value}"
                        else:
                            provider_info = f"Прямая привязка: {binding}"
                        
                        logger.debug(f" - Ключ: {key}  -->  {provider_info}")
                    logger.debug("DEBUG: Конец списка привязок.")
                else:
                    logger.warning("WARNING: Инжектор не найден или не имеет атрибута _bindings.")
            except Exception as e:
                logger.error(f"ERROR: Ошибка при инспекции инжектора: {e}", exc_info=True)
            # --- КОНЕЦ БЛОКА ОТЛАДКИ INJECTOR ---

            cog_instance = inject.instance(cog_class)
            logger.debug(f"DEBUG: Экземпляр кога {cog_class.__name__} успешно создан.")
            
            await self.bot.add_cog(cog_instance)
            logger.debug(f"DEBUG: Ког {cog_class.__name__} успешно добавлен в бота.")

            self.loaded_cogs.add(module_name)
            logger.success(f"⬆️ Загружен: {module_name}")
            # COGS_LOAD_SUCCESS.inc() # Prometheus
            # COGS_LOADED_COUNT.set(len(self.loaded_cogs)) # Prometheus
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кога {module_name}", exc_info=True)
            # COGS_LOAD_FAILURES.labels(reason='exception').inc() # Prometheus
            return False

    async def reload_cogs(self):
        logger.info("🔄 Начинается перезагрузка всех загруженных когов.")
        # COGS_RELOAD_ATTEMPTS.inc() # Prometheus
        initial_loaded_cogs = list(self.loaded_cogs) # Итерируемся по копии
        reloaded_count = 0

        for cog_module_name in initial_loaded_cogs:
            logger.debug(f"DEBUG: Попытка перезагрузить ког: {cog_module_name}")
            try:
                # Получаем экземпляр кога по имени, чтобы удалить
                cog_name_from_module = cog_module_name.split('.')[-1] # Имя класса обычно совпадает с именем модуля без пути
                cog_instance = self.bot.get_cog(cog_name_from_module) # Discord.py ищет по qualified_name или имени
                
                if cog_instance:
                    await self.bot.remove_cog(cog_instance.qualified_name)
                    logger.debug(f"⬇️ Удален ког для перезагрузки: {cog_instance.qualified_name}")
                    # self.loaded_cogs.remove(cog_module_name) # Не удаляем здесь, чтобы список оставался для for-цикла
                else:
                    logger.warning(f"WARNING: Не удалось найти экземпляр кога '{cog_name_from_module}' для удаления перед перезагрузкой. Возможно, он уже был удален или не был загружен.")

                # Принудительная перезагрузка модуля, чтобы получить свежий код
                spec = importlib.util.find_spec(cog_module_name)
                if spec:
                    lib = importlib.import_module(cog_module_name)
                    importlib.reload(lib)
                    logger.debug(f"🔄 Модуль {cog_module_name} перезагружен.")
                    
                    # Ищем класс кога в перезагруженном модуле
                    cog_class = None
                    for name, obj in inspect.getmembers(lib):
                        if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj != commands.Cog:
                            cog_class = obj
                            logger.debug(f"DEBUG: Класс кога '{cog_class.__name__}' найден в перезагруженном модуле.")
                            break
                    
                    if cog_class:
                        new_cog_instance = inject.instance(cog_class) # Создаем новый экземпляр через DI
                        await self.bot.add_cog(new_cog_instance) # Добавляем новый экземпляр
                        self.loaded_cogs.add(cog_module_name) # Снова добавляем в список загруженных
                        logger.success(f"🔄 Перезагружен и заново добавлен: {cog_module_name}")
                        reloaded_count += 1
                        # COGS_RELOAD_SUCCESS.inc() # Prometheus
                        # COGS_LOADED_COUNT.set(len(self.loaded_cogs)) # Prometheus
                    else:
                        logger.error(f"❌ Не удалось найти класс кога в перезагруженном модуле {cog_module_name}.")
                        # COGS_RELOAD_FAILURES.inc() # Prometheus
                else:
                    logger.error(f"❌ Не удалось найти спецификацию для перезагрузки модуля кога: {cog_module_name}")
                    # COGS_RELOAD_FAILURES.inc() # Prometheus

            except Exception as e:
                logger.error(f"❌ Ошибка перезагрузки кога {cog_module_name}", exc_info=True)
                # COGS_RELOAD_FAILURES.inc() # Prometheus
        logger.info(f"✅ Перезагрузка когов завершена. Успешно перезагружено: {reloaded_count} из {len(initial_loaded_cogs)}")