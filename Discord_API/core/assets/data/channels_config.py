# Discord_API/core/assets/data/channels_config.py




# Discord_API/core/assets/data/channels_config.py

import json
import os

from Discord_API.config.logging.logging_setup_discod import logger # Используем ваш указанный путь
discord_entity_service_logger = logger.getChild(__name__) # Создаем дочерний логгер для этого модуля

# ОПРЕДЕЛЯЕМ ПУТЬ ОТНОСИТЕЛЬНО ЭТОГО ЖЕ ФАЙЛА
_file_path = os.path.join(os.path.dirname(__file__), 'channels_config.json')

CHANNELS_CONFIG: dict = {}

try:
    with open(_file_path, 'r', encoding='utf-8') as f:
        CHANNELS_CONFIG = json.load(f)
    logger.info(f"Конфигурация каналов успешно загружена из {_file_path}")
except FileNotFoundError:
    logger.error(f"Файл конфигурации каналов не найден: {_file_path}. Убедитесь, что channels_config.json существует.")
    raise # Важно пробросить
except json.JSONDecodeError as e:
    logger.error(f"Ошибка парсинга JSON в файле {_file_path}: {e}. Убедитесь, что JSON валиден.")
    raise
except Exception as e:
    logger.error(f"Неизвестная ошибка при загрузке channels_config.json: {e}", exc_info=True)
    raise