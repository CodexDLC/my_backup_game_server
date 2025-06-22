# Discord_API\config\logging\logging_setup.py

import logging

# Убедитесь, что пути импорта верны для вашей структуры проекта
from Discord_API.config.logging.logging_config import loggerConfig
from Discord_API.config.logging.logging_handlers import get_console_handler, get_file_handler

# 1. Создаем объект конфигурации логгера
config = loggerConfig()
# 2. Получаем наш основной логгер бота (с новым именем "discord_bot")
logger = config.get_logger() # ✅ Имя логгера бота

# 3. Устанавливаем базовый уровень для логгера бота
logger.setLevel(logging.DEBUG)

# --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: УДАЛЯЕМ УСЛОВИЕ if not logger.hasHandlers() ---
# Это гарантирует, что все обработчики будут всегда добавлены,
# независимо от состояния логгера при импорте модуля.
logger.propagate = False # Остается False, чтобы избежать дублирования с корневым логгером Python

# 4. Добавляем обработчики (хэндлеры)
logger.addHandler(get_console_handler(config.console_log_level))
logger.addHandler(get_file_handler(config.debug_log_file, config.debug_log_level, config.max_file_size, config.backup_count))
logger.addHandler(get_file_handler(config.info_log_file, config.info_log_level, config.max_file_size, config.backup_count))
logger.addHandler(get_file_handler(config.warning_log_file, config.warning_log_level, config.max_file_size, config.backup_count))
logger.addHandler(get_file_handler(config.error_log_file, config.error_log_level, config.max_file_size, config.backup_count))
logger.addHandler(get_file_handler(config.critical_log_file, config.critical_log_level, config.max_file_size, config.backup_count))
logger.addHandler(get_file_handler(config.exception_log_file, config.exception_log_level, config.max_file_size, config.backup_count))

# Сообщение об успешной инициализации логгирования
logger.info("✅ Логирование бота инициализировано.")
