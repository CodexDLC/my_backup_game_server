# game_server/Logic/InfrastructureLogic/logging/logging_config.py

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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.log_dir = os.path.join(project_root, "logs") 

        container_id = os.getenv('CONTAINER_ID', 'default') 

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
        self.app_logger = logging.getLogger("game_server_app_logger") # <--- ИЗМЕНЕНО: Имя логгера
        self.app_logger.setLevel(logging.DEBUG)
        self._disable_sqlalchemy_logs()

    def get_logger(self):
        return self.app_logger # <--- ИЗМЕНЕНО: Возвращаем app_logger

    def _disable_sqlalchemy_logs(self):
        sql_loggers = [
            "sqlalchemy",
            "sqlalchemy.engine",
            "sqlalchemy.pool",
            "sqlalchemy.orm",
            "asyncpg",
        ]
        for sql_logger in sql_loggers:
            logging.getLogger(sql_logger).setLevel(logging.WARNING) # Уровень WARNING