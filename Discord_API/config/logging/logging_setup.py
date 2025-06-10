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
#    Уровень DEBUG означает, что логгер будет обрабатывать ВСЕ сообщения,
#    начиная от DEBUG и выше. Фильтрация на INFO/WARNING/ERROR будет
#    происходить на уровне каждого отдельного файлового обработчика.
logger.setLevel(logging.DEBUG)

# --- ДОБАВИТЬ ЭТУ СТРОКУ ---
logger.propagate = False
# ---------------------------


# 4. Добавляем обработчики (хэндлеры) только если они еще не добавлены
#    Это важно, чтобы избежать дублирования логов при повторном импорте
if not logger.hasHandlers():
    # Консольный обработчик (например, будет выводить INFO и выше в консоль)
    logger.addHandler(get_console_handler(config.console_log_level))

    # Файловые обработчики с ротацией
    # debug.log будет содержать ВСЕ сообщения (начиная с DEBUG)
    logger.addHandler(get_file_handler(config.debug_log_file, config.debug_log_level, config.max_file_size, config.backup_count))
    # info.log будет содержать сообщения INFO и выше
    logger.addHandler(get_file_handler(config.info_log_file, config.info_log_level, config.max_file_size, config.backup_count))
    # warning.log будет содержать сообщения WARNING и выше
    logger.addHandler(get_file_handler(config.warning_log_file, config.warning_log_level, config.max_file_size, config.backup_count))
    # error.log будет содержать сообщения ERROR и выше
    logger.addHandler(get_file_handler(config.error_log_file, config.error_log_level, config.max_file_size, config.backup_count))
    # critical.log будет содержать сообщения CRITICAL и выше
    logger.addHandler(get_file_handler(config.critical_log_file, config.critical_log_level, config.max_file_size, config.backup_count))
    # exception.log (часто дублирует ERROR, но полезен для отлова необработанных исключений)
    logger.addHandler(get_file_handler(config.exception_log_file, config.exception_log_level, config.max_file_size, config.backup_count))

    # Сообщение об успешной инициализации логгирования
    logger.info("✅ Логирование бота инициализировано.") # ✅ Обновлено сообщение