import logging
from game_server.services.logging.logging_config import loggerConfig
from game_server.services.logging.logging_handlers import get_console_handler, get_file_handler

config = loggerConfig()
logger = config.get_logger()


if not logger.hasHandlers():
    logger.addHandler(get_console_handler(config.console_log_level))
    logger.addHandler(get_file_handler(config.debug_log_file, config.debug_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.info_log_file, config.info_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.warning_log_file, config.warning_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.error_log_file, config.error_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.critical_log_file, config.critical_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.exception_log_file, config.exception_log_level, config.max_file_size, config.backup_count))

    

    logger.info("✅ Логирование инициализировано.")



