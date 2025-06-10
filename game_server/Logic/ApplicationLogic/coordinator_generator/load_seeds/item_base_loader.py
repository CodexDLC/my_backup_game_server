# game_server/Logic/ApplicationLogic/coordinator_generator/load_seeds/item_base_loader.py

import json
from pathlib import Path
from typing import Dict, Any # Добавлено для возвращаемого типа


from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.yaml_readers import YamlReader
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import ITEM_BASE_YAML_PATH # DEFAULT_TTL_STATIC_REF_DATA и REDIS_KEY_ITEM_DATA_BASE больше не нужны здесь
from game_server.services.logging.logging_setup import logger

# 🔥 УДАЛЕНИЕ ИМПОРТА: reference_data_cache_manager больше не нужен здесь 🔥
# from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_cache_manager import reference_data_cache_manager


class ItemBaseLoader:
    def __init__(self):
        self.yaml_reader = YamlReader()

    async def _read_and_combine_yamls(self, directory: Path) -> Dict[str, Any]:
        combined_data: Dict[str, Any] = {}
        if not directory.is_dir():
            logger.error(f"Директория с item_base не найдена по пути: {directory}")
            return combined_data
        yaml_files = list(directory.glob('*.yml'))
        logger.info(f"Найдено {len(yaml_files)} YAML-файлов item_base в '{directory}'.")
        for file_path in yaml_files:
            items_list = await self.yaml_reader.get_items_from_yaml(file_path, pk_column_name='sub_category_code')
            for item_dict in items_list:
                key = item_dict.get('sub_category_code')
                if key:
                    if key in combined_data:
                        logger.warning(f"Найден дублирующийся ключ item_base '{key}' в файле '{file_path}'. Он перезапишет предыдущее значение.")
                    if 'names' in item_dict and isinstance(item_dict['names'], dict):
                        logger.debug(f"Имена 'names' для '{key}' загружены без нормализации. Ключи: {list(item_dict['names'].keys())[:2]}")
                    combined_data[key] = item_dict
        logger.info(f"Успешно объединено {len(combined_data)} записей item_base из всех файлов.")
        return combined_data

    # 🔥 ИЗМЕНЕНИЕ: Метод теперь возвращает данные, а не кэширует их 🔥
    async def load_and_cache(self) -> Dict[str, Any]: # Изменено на Dict[str, Any]
        """
        Загружает данные item_base из YAML-файлов и возвращает их.
        Кэширование будет выполнено вызывающим кодом (ReferenceDataCacheManager).
        """
        base_path = Path(ITEM_BASE_YAML_PATH)

        logger.info(f"Запуск загрузки item_base YAML-файлов из '{base_path}'...")
        try:
            all_item_bases = await self._read_and_combine_yamls(base_path)
            if not all_item_bases:
                logger.warning("Данные item_base не найдены или не загружены.")
                return {} # Возвращаем пустой словарь, если данные не найдены
            
            logger.info(f"Успешно загружено {len(all_item_bases)} записей item_base из YAML-файлов.")
            # 🔥 НОВОЕ: Логирование содержимого для проверки id_field 🔥
            for i, (key, item_data) in enumerate(list(all_item_bases.items())[:5]): # Логируем первые 5 для примера
                logger.debug(f"ItemBase #{i+1} (key: {key}): sub_category_code={item_data.get('sub_category_code')}, content_sample={str(item_data)[:100]}...")
                if item_data.get('sub_category_code') is None:
                    logger.critical(f"Критическая ошибка: В ItemBase '{key}' отсутствует 'sub_category_code'!")
            return all_item_bases
        except Exception as e:
            logger.error(f"Ошибка при загрузке item_base: {e}")
            return {}