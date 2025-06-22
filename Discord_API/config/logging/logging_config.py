# Discord_API\config\logging\logging_config.py
import os
import logging

SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success

class loggerConfig:
    def __init__(self):
        # project_root будет /app/Discord_API (корневая папка проекта бота внутри контейнера)
        # НО: логи мы монтируем в /app/game_server/logs в docker-compose.yml.
        # Поэтому, log_dir должен указывать на эту смонтированную директорию.
        # Мы будем использовать абсолютный путь, как в других сервисах, чтобы избежать путаницы.
        # Предполагаем, что Dockerfile Discord-бота тоже копирует свой код в /app/Discord_API
        # и что /app/game_server/logs является корневой точкой монтирования логов для всего проекта
        
        # Директория логов внутри контейнера, куда Docker Compose монтирует тома.
        # Это должен быть путь, который вы указали справа в volumes в docker-compose.yml,
        # например, /app/game_server/logs
        self.log_dir = "/app/game_server/logs" 
        
        # УДАЛЕНО: os.makedirs(self.log_dir, exist_ok=True)
        # Создание директории и установка прав будет делегировано get_file_handler.

        container_id = os.getenv('CONTAINER_ID', 'default') # Получаем ID контейнера для имени файла лога

        # Файлы логов теперь будут находиться прямо в self.log_dir
        # с префиксом, указывающим на контейнер:
        # Например: /app/game_server/logs/discord_bot_service_debug.log
        self.debug_log_file = os.path.join(self.log_dir, f'{container_id}_debug.log')
        self.info_log_file = os.path.join(self.log_dir, f'{container_id}_info.log')
        self.warning_log_file = os.path.join(self.log_dir, f'{container_id}_warning.log')
        self.error_log_file = os.path.join(self.log_dir, f'{container_id}_error.log')
        self.critical_log_file = os.path.join(self.log_dir, f'{container_id}_critical.log')
        self.exception_log_file = os.path.join(self.log_dir, f'{container_id}_exception.log')

        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.backup_count = 3

        self.console_log_level = logging.INFO
        self.debug_log_level = logging.DEBUG
        self.info_log_level = logging.INFO
        self.warning_log_level = logging.WARNING
        self.error_log_level = logging.ERROR
        self.critical_log_level = logging.CRITICAL
        self.exception_log_level = logging.ERROR
        
        self.sql_echo = os.getenv("SQL_ECHO", "False").lower() == "true"
        self.logger = logging.getLogger("discord_bot")
        self._disable_third_party_logs()

    def _disable_third_party_logs(self):
        """Отключает слишком подробные логи от сторонних библиотек."""
        # ... (ваш существующий код для _disable_third_party_logs) ...
        # SQL логи
        sql_loggers = [
            "sqlalchemy",
            "sqlalchemy.engine",
            "sqlalchemy.pool",
            "sqlalchemy.orm",
            "asyncpg",
            "aiosqlite"
        ]
        for logger_name in sql_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING) # Только WARNING и CRITICAL
            logger.propagate = False # Отключаем распространение логов вверх

        # Discord.py логи (очень шумные на DEBUG)
        discord_loggers = [
            "discord",
            "discord.http",
            "discord.gateway"
        ]
        for logger_name in discord_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO) # INFO для основной работы Discord
            logger.propagate = False

        # Другие потенциально шумные библиотеки
        other_loggers = [
            "aiohttp",
            "asyncio",
            "urllib3", # для requests
            "websockets"
        ]
        for logger_name in other_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO) # INFO для этих библиотек
            logger.propagate = False

    def get_logger(self):
        """Возвращает настроенный логгер."""
        return self.logger
