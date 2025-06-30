# game_server/utils/load_seeds/yaml_readers.py

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from game_server.config.logging.logging_setup import app_logger as logger

class YamlReader:
    @staticmethod
    async def read_and_parse_yaml(file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Базовая функция для чтения и парсинга YAML-файла.
        В случае ошибки возвращает None и логирует проблему.
        """
        try:
            logger.info(f"📂 Чтение YAML-файла: {file_path.name}")
            with open(str(file_path), 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)
                logger.info(f"✅ Успешно загружены данные из '{file_path.name}'.")
                return loaded_data
        except FileNotFoundError:
            logger.error(f"❌ Файл не найден: {file_path}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"❌ Ошибка парсинга YAML в файле {file_path}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при чтении {file_path}: {e}", exc_info=True)
            return None

    @staticmethod
    async def get_items_from_yaml(file_path: Path, pk_column_name: str) -> List[Dict[str, Any]]:
        """
        Читает YAML и адаптирует его содержимое.
        ❗️ ВАЖНО: Теперь вызывает исключение при неверном формате.
        """
        loaded_data = await YamlReader.read_and_parse_yaml(file_path)

        # Если файл не удалось прочитать или распарсить
        if loaded_data is None:
            raise RuntimeError(f"Критическая ошибка: не удалось прочитать или распарсить файл '{file_path.name}'.")

        # 👇 ИЗМЕНЕНИЕ: Проверяем наличие ключа 'data' и выбрасываем исключение, если его нет
        if 'data' not in loaded_data:
            logger.critical(f"🚨 Критическая ошибка: В файле '{file_path.name}' отсутствует обязательный корневой ключ 'data'.")
            raise RuntimeError(f"Неверный формат сида в файле {file_path.name}: отсутствует ключ 'data'.")

        data_content = loaded_data['data']

        # Если 'data' пуст (data: ), это не ошибка, просто нет данных.
        if not data_content:
            logger.warning(f"⚠️ Файл '{file_path.name}' содержит пустой ключ 'data'.")
            return []

        items_to_process: List[Dict[str, Any]] = []
        if isinstance(data_content, list):
            items_to_process = data_content

        elif isinstance(data_content, dict):
            if not pk_column_name:
                raise RuntimeError(f"Не указан pk_column_name для обработки словаря в '{file_path.name}'.")
            for key, item_dict in data_content.items():
                if not isinstance(item_dict, dict):
                    logger.warning(f"Элемент '{key}' в словаре '{file_path.name}' не является словарем. Пропускаем.")
                    continue
                item_dict[pk_column_name] = key
                items_to_process.append(item_dict)
        else:
            # 👇 ИЗМЕНЕНИЕ: Выбрасываем исключение при неверном типе данных
            logger.critical(f"🚨 Критическая ошибка: Неподдерживаемый формат данных в '{file_path.name}': ожидался список или словарь, получен {type(data_content)}.")
            raise RuntimeError(f"Неверный формат данных в файле {file_path.name}.")
        
        return items_to_process