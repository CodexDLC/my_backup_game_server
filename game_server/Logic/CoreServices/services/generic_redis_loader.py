# game_server/Logic/CoreServices/services/generic_redis_loader.py

from pathlib import Path
from typing import Dict, Any, List, TypeVar, Type, Optional, Union
from pydantic import BaseModel, ValidationError

from game_server.Logic.CoreServices.utils.yaml_readers import YamlReader
from game_server.config.logging.logging_setup import app_logger as logger

PydanticDTO = TypeVar('PydanticDTO', bound=BaseModel)

class GenericRedisLoader:
    def __init__(self):
        logger.info("✅ GenericRedisLoader (CoreService) инициализирован.")

    async def load_from_directory(
        self,
        directory_path: str,
        dto_type: Type[PydanticDTO]
    ) -> List[PydanticDTO]:
        base_path = Path(directory_path)
        logger.info(f"🚀 Запуск GenericRedisLoader для директории '{base_path}'...")
        
        all_dtos: List[PydanticDTO] = []
        if not base_path.is_dir():
            logger.error(f"Директория не найдена: {base_path}")
            return all_dtos

        yaml_files = sorted(list(base_path.glob('*.yml')))
        logger.info(f"Найдено {len(yaml_files)} YAML-файлов для '{dto_type.__name__}'.")

        for file_path in yaml_files:
            try:
                full_yaml_content: Optional[Dict[str, Any]] = await YamlReader.read_and_parse_yaml(file_path)
                
                if full_yaml_content is None:
                    continue 

                # ВСЕГДА ОЖИДАЕМ, ЧТО ДАННЫЕ НАХОДЯТСЯ ПОД КЛЮЧОМ 'data'
                if 'data' not in full_yaml_content:
                    logger.error(f"❌ Файл '{file_path.name}' не содержит обязательного корневого ключа 'data'. Пропускаем.")
                    continue
                
                raw_items_data = full_yaml_content['data']
                items_to_process_list: List[Dict[str, Any]] = []

                # Теперь обрабатываем то, что находится под 'data'
                if isinstance(raw_items_data, list):
                    # Если 'data' содержит список словарей (как GameLocation)
                    logger.debug(f"Файл '{file_path.name}': 'data' содержит список.")
                    items_to_process_list = raw_items_data

                elif isinstance(raw_items_data, dict):
                    # Если 'data' содержит словарь (как ItemBase)
                    logger.debug(f"Файл '{file_path.name}': 'data' содержит словарь (ключ: item_data).")
                    if 'item_code' not in dto_type.model_fields:
                        logger.error(f"Ошибка: DTO '{dto_type.__name__}' не имеет поля 'item_code', но файл '{file_path.name}' имеет формат 'item_code: dict' под ключом 'data'. Пропускаем.")
                        continue # Пропускаем файл, если DTO не готова к этому формату

                    for item_code_key, item_data_dict in raw_items_data.items():
                        if not isinstance(item_data_dict, dict):
                            logger.warning(f"Элемент '{item_code_key}' в файле '{file_path.name}' не является словарем. Пропускаем.")
                            continue
                        
                        # Добавляем item_code в данные для DTO
                        processed_item_dict = {"item_code": item_code_key, **item_data_dict}
                        items_to_process_list.append(processed_item_dict)
                else:
                    logger.error(f"Неподдерживаемый тип данных под ключом 'data' в файле '{file_path.name}': ожидался список или словарь, получен {type(raw_items_data)}. Пропускаем.")
                    continue
                
                # Теперь валидируем собранные элементы
                for item_dict in items_to_process_list:
                    try:
                        item_dto = dto_type(**item_dict)
                        all_dtos.append(item_dto)
                    except ValidationError as e:
                        logger.error(f"Ошибка валидации Pydantic для элемента из '{file_path.name}' ({item_dict.get('item_code', 'N/A')}): {e.errors()}")
                        continue
                    except Exception as e:
                        logger.error(f"Непредвиденная ошибка при валидации элемента из '{file_path.name}' ({item_dict.get('item_code', 'N/A')}): {e}", exc_info=True)
                        continue

            except Exception as e:
                logger.error(f"Критическая ошибка при обработке файла '{file_path}': {e}. Пропускаем.", exc_info=True)
                continue
        
        logger.info(f"✅ Успешно загружено и валидировано {len(all_dtos)} записей типа '{dto_type.__name__}'.")
        return all_dtos