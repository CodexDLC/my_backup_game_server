import os
import logging


SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success  # добавить метод здесь



class loggerConfig:
    def __init__(self):
        container_id = os.getenv('CONTAINER_ID', 'default')
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_root = os.path.join(project_root, "logs", container_id)
        os.makedirs(log_root, exist_ok=True)

        self.log_dir = log_root
        self.debug_log_file = os.path.join(self.log_dir, 'debug.log')
        self.info_log_file = os.path.join(self.log_dir, 'info.log')
        self.warning_log_file = os.path.join(self.log_dir, 'warning.log')
        self.error_log_file = os.path.join(self.log_dir, 'error.log')
        self.critical_log_file = os.path.join(self.log_dir, 'critical.log')
        self.exception_log_file = os.path.join(self.log_dir, 'exception.log')

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
        self.logger = logging.getLogger("game_server")  # ✅ Теперь `self.logger` сохранён
        self.logger.setLevel(logging.DEBUG)
        # ✅ Отключаем лишние логи SQLAlchemy
        self._disable_sqlalchemy_logs()

    def _disable_sqlalchemy_logs(self):
        """Оставляет только `WARNING` и `CRITICAL`, скрывает `INFO` и `DEBUG`."""
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
            logger.setLevel(logging.WARNING)  # 📌 Только `WARNING` и `CRITICAL`
            logger.propagate = False


    def get_logger(self):
        """Возвращает настроенный логгер."""
        return self.logger


