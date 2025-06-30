# game_server/app_discord_bot/config/assets/data/channels_config.py

import json
import os
from typing import Dict, Any

from game_server.config.logging.logging_setup import app_logger as logger

# Определяем путь к папке с файлами конфигурации лейаутов
_layouts_dir = os.path.join(os.path.dirname(__file__), 'layouts')

CHANNELS_CONFIG: Dict[str, Any] = {}

# Список файлов для загрузки и их ключей в итоговой конфигурации
_config_files = {
    "hub_layout": "hub_layout.json",
    "game_server_layout": "game_server_layout.json",
    "permissions_sets": "permissions_config.json", # Переименовываем ключ для соответствия старому формату
    "emojis_formatting": "emojis_formatting_config.json" # Новый раздел для эмодзи и форматирования
}

logger.info(f"Начало загрузки конфигураций лейаутов из {_layouts_dir}...")

try:
    for config_key, filename in _config_files.items():
        file_path = os.path.join(_layouts_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                CHANNELS_CONFIG[config_key] = json.load(f)
            logger.info(f"✅ Конфигурация '{filename}' успешно загружена.")
        except FileNotFoundError:
            logger.critical(f"❌ Критическая ошибка: Файл конфигурации не найден: {file_path}. Убедитесь, что все файлы лейаутов существуют.")
            raise # Критическая ошибка, если файл не найден
        except json.JSONDecodeError as e:
            logger.critical(f"❌ Критическая ошибка: Ошибка парсинга JSON в файле {file_path}: {e}. Убедитесь, что JSON валиден.")
            raise # Критическая ошибка, если JSON невалиден
        except Exception as e:
            logger.critical(f"❌ Критическая ошибка: Неизвестная ошибка при загрузке {file_path}: {e}", exc_info=True)
            raise # Критическая ошибка по любой другой причине

    logger.info("✅ Все конфигурации лейаутов успешно загружены и объединены.")

except Exception as e:
    logger.critical(f"🚨 Критическая ошибка при инициализации CHANNELS_CONFIG: {e}", exc_info=True)
    raise # Пробрасываем ошибку дальше, так как без конфига работать нельзя

