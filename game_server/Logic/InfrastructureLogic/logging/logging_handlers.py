# game_server/Logic/InfrastructureLogic/logging/logging_handlers.py

import logging
import sys
import colorlog
import os 
from logging.handlers import RotatingFileHandler

handler = logging.StreamHandler(sys.stdout)
formatter = formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_console_handler(level):
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s | %(blue)s%(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red'
        }
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler

def get_file_handler(path, level, max_size, backups):
    log_dir = os.path.dirname(path)
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            os.chmod(log_dir, 0o777) 
        else:
            current_mode = os.stat(log_dir).st_mode
            if not (current_mode & 0o777 == 0o777): 
                os.chmod(log_dir, 0o777)
    except OSError as e:
        # Используем базовый логгер для этой ошибки, чтобы избежать рекурсии
        logging.getLogger(__name__).error(f"Не удалось создать директорию логов или установить права для '{log_dir}': {e}", exc_info=True) 

    file_handler = RotatingFileHandler(path, maxBytes=max_size, backupCount=backups, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    return file_handler