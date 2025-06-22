# game_server/Logic/InfrastructureLogic/logging/logging_setup.py

# ИМПОРТЫ: ОБНОВЛЕНЫ ПУТИ
from game_server.Logic.InfrastructureLogic.logging.logging_config import loggerConfig
from game_server.Logic.InfrastructureLogic.logging.logging_handlers import get_console_handler, get_file_handler


config = loggerConfig()
app_logger = config.get_logger()

app_logger.propagate = False

# ИСПРАВЛЕНО: Раскомментирована проверка hasHandlers()
# Это гарантирует, что обработчики будут добавлены только один раз
if not app_logger.hasHandlers():
    # Добавляем консольный обработчик
    app_logger.addHandler(get_console_handler(config.console_log_level))

    # Добавляем файловые обработчики для разных уровней
    app_logger.addHandler(get_file_handler(config.debug_log_file, config.debug_log_level, config.max_file_size, config.backup_count))
    app_logger.addHandler(get_file_handler(config.info_log_file, config.info_log_level, config.max_file_size, config.backup_count))
    app_logger.addHandler(get_file_handler(config.warning_log_file, config.warning_log_level, config.max_file_size, config.backup_count))
    app_logger.addHandler(get_file_handler(config.error_log_file, config.error_log_level, config.max_file_size, config.backup_count))
    app_logger.addHandler(get_file_handler(config.critical_log_file, config.critical_log_level, config.max_file_size, config.backup_count))
    app_logger.addHandler(get_file_handler(config.exception_log_file, config.exception_log_level, config.max_file_size, config.backup_count))

# Экспорт app_logger для использования в других модулях
# from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger
