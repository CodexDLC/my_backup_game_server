import logging
import sys
import colorlog
from logging.handlers import RotatingFileHandler
import os

class LoggingConfig:
    def __init__(self):
        # Папка для логов
        self.log_dir = os.path.join(os.path.dirname(__file__), 'log')
        os.makedirs(self.log_dir, exist_ok=True)  # Создаем папку для логов, если её нет

        # Пути для лог-файлов
        self.debug_log_file = os.path.join(self.log_dir, 'debug.log')    # Логи DEBUG
        self.info_log_file = os.path.join(self.log_dir, 'info.log')      # Логи INFO
        self.warning_log_file = os.path.join(self.log_dir, 'warning.log') # Логи WARNING
        self.error_log_file = os.path.join(self.log_dir, 'error.log')    # Логи ERROR
        self.critical_log_file = os.path.join(self.log_dir, 'critical.log')  # Логи CRITICAL
        self.exception_log_file = os.path.join(self.log_dir, 'exception.log') # Логи EXCEPTION

        # Максимальный размер файла логов
        self.max_file_size = 5 * 1024 * 1024  # 5MB

        # Число резервных файлов
        self.backup_count = 3

        # Уровни логирования
        self.console_log_level = logging.INFO
        self.debug_log_level = logging.DEBUG
        self.info_log_level = logging.INFO
        self.warning_log_level = logging.WARNING
        self.error_log_level = logging.ERROR
        self.critical_log_level = logging.CRITICAL
        self.exception_log_level = logging.ERROR

        # Логгер
        self.logger = logging.getLogger("game_server")
        self.logger.setLevel(logging.DEBUG)

    def setup_logging(self):
        """Настроить логирование для разных типов логов."""

        # Проверяем, настроены ли обработчики (чтобы избежать повторной конфигурации)
        if self.logger.hasHandlers():
            return  # Логгер уже настроен

        # Форматирование для консоли
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s | %(blue)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            }
        )

        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_log_level)
        console_handler.setFormatter(console_formatter)

        # Форматирование для файлов
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Обработчик для логирования DEBUG
        debug_file_handler = RotatingFileHandler(self.debug_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        debug_file_handler.setLevel(self.debug_log_level)
        debug_file_handler.setFormatter(file_formatter)

        # Обработчик для логирования INFO
        info_file_handler = RotatingFileHandler(self.info_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        info_file_handler.setLevel(self.info_log_level)
        info_file_handler.setFormatter(file_formatter)

        # Обработчик для логирования WARNING
        warning_file_handler = RotatingFileHandler(self.warning_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        warning_file_handler.setLevel(self.warning_log_level)
        warning_file_handler.setFormatter(file_formatter)

        # Обработчик для логирования ERROR
        error_file_handler = RotatingFileHandler(self.error_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        error_file_handler.setLevel(self.error_log_level)
        error_file_handler.setFormatter(file_formatter)

        # Обработчик для логирования CRITICAL
        critical_file_handler = RotatingFileHandler(self.critical_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        critical_file_handler.setLevel(self.critical_log_level)
        critical_file_handler.setFormatter(file_formatter)

        # Обработчик для логирования EXCEPTION
        exception_file_handler = RotatingFileHandler(self.exception_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count)
        exception_file_handler.setLevel(self.exception_log_level)
        exception_file_handler.setFormatter(file_formatter)

        # Добавляем обработчики
        self.logger.addHandler(console_handler)         # Консоль
        self.logger.addHandler(debug_file_handler)      # Логирование для DEBUG
        self.logger.addHandler(info_file_handler)       # Логирование для INFO
        self.logger.addHandler(warning_file_handler)    # Логирование для WARNING
        self.logger.addHandler(error_file_handler)      # Логирование для ERROR
        self.logger.addHandler(critical_file_handler)   # Логирование для CRITICAL
        self.logger.addHandler(exception_file_handler)  # Логирование для EXCEPTION

        self.logger.info("✅ Логирование для всех типов успешно настроено!")

# Настройка логирования для всех типов
logging_config = LoggingConfig()
logging_config.setup_logging()
logger = logging_config.logger
