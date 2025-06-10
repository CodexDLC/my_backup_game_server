# game_server/utils/load_seeds/yaml_readers.py

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from game_server.services.logging.logging_setup import logger

class YamlReader:
    @staticmethod
    async def read_and_parse_yaml(file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Базовая функция для чтения и парсинга YAML-файла.
        Возвращает None в случае ошибки чтения или парсинга.
        """
        try:
            logger.debug(f"📂 Попытка загрузить YAML: {file_path}")
            with open(str(file_path), 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)
                logger.debug(f"🔍 Загружены данные из YAML '{file_path}': тип: {type(loaded_data)}, ключи: {loaded_data.keys() if isinstance(loaded_data, dict) else 'N/A'}")
                return loaded_data
        except FileNotFoundError:
            logger.warning(f"⚠️ Файл не найден: {file_path}. Пропуск загрузки.")
            return None
        except yaml.YAMLError as e:
            logger.error(f"❌ Ошибка парсинга YAML в файле {file_path}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при загрузке {file_path}: {str(e)}", exc_info=True)
            return None

    @staticmethod
    async def get_items_from_yaml(file_path: Path, pk_column_name: str) -> List[Dict[str, Any]]:
        """
        Читает YAML-файл и адаптирует его содержимое в список словарей.
        Поддерживает два формата корневого ключа 'data':
        1. data: [ {item1}, {item2} ] (список словарей)
        2. data: { key1: {item1_data}, key2: {item2_data} } (словарь словарей, где ключи - это ID)

        :param file_path: Путь к YAML-файлу.
        :param pk_column_name: Имя первичного ключа модели, используется для формата "словарь словарей".
        :return: Список словарей, готовых для вставки/обновления.
        """
        loaded_data = await YamlReader.read_and_parse_yaml(file_path)
        items_to_process: List[Dict[str, Any]] = []

        if not loaded_data or 'data' not in loaded_data:
            logger.debug(f"⚠️ Файл '{file_path}' пуст или отсутствует корневой ключ 'data'.")
            return items_to_process # Возвращаем пустой список

        data_content = loaded_data['data']

        if isinstance(data_content, list):
            items_to_process = data_content
            logger.debug(f"✅ Формат 'data' в '{file_path}': список объектов. Элементов: {len(items_to_process)}")
        elif isinstance(data_content, dict):
            logger.debug(f"✅ Формат 'data' в '{file_path}': словарь объектов. Преобразуем в список, используя ключи как '{pk_column_name}'.")
            
            # Проверяем, что pk_column_name предоставлен, если мы работаем со словарем
            if not pk_column_name:
                logger.error(f"❌ Не указано имя первичного ключа (pk_column_name) для обработки словаря в '{file_path}'. Пропуск.")
                return []

            for key, item_dict in data_content.items():
                if not isinstance(item_dict, dict):
                    logger.warning(f"⚠️ Элемент '{key}' в 'data' словаре '{file_path}' не является словарем. Пропускаем.")
                    continue
                # Добавляем ключ словаря как поле ID в сам элемент данных
                item_dict[pk_column_name] = key
                items_to_process.append(item_dict)
            logger.debug(f"📊 Преобразовано элементов из словаря в '{file_path}': {len(items_to_process)}")
        else:
            logger.error(f"❌ Неподдерживаемый формат данных в '{file_path}': ожидался список или словарь объектов в ключе 'data', получен {type(data_content)}.")
            return []
        
        return items_to_process