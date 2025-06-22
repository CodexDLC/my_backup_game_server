import logging
import sys
import colorlog
import os # Импортируем os
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
    # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ (ПОВТОРНОЕ ВНЕДРЕНИЕ) ---
    # Гарантируем существование директории и устанавливаем права 777 перед созданием файла
    log_dir = os.path.dirname(path)
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            # Принудительно устанавливаем права на чтение/запись/выполнение для всех
            # Это должно обойти любые проблемы с правами, наложенные Docker Desktop/WSL.
            os.chmod(log_dir, 0o777) 
        else:
            # Если директория существует, также убедимся, что у нее есть нужные права.
            # Это нужно, если Docker Desktop создал ее с ограниченными правами.
            current_mode = os.stat(log_dir).st_mode
            if not (current_mode & 0o777 == 0o777): # Проверяем, если права не 777
                os.chmod(log_dir, 0o777)
    except OSError as e:
        # Логируем ошибку, но не поднимаем ее, чтобы не сломать приложение
        # Здесь мы не можем использовать наш основной логгер, так как он может быть еще не инициализирован
        # Используем стандартный logging.error
        logging.error(f"Не удалось создать директорию логов или установить права для '{log_dir}': {e}", exc_info=True)
        # Если здесь ошибка прав, то RotatingFileHandler все равно выдаст ошибку
        # Но это даст более точное сообщение в логах.
    # --- КОНЕЦ КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(path, maxBytes=max_size, backupCount=backups)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler
