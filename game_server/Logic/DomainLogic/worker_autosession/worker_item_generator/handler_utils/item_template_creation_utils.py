# game_server/Logic/DomainLogic/handlers_template/worker_item_generator/item_batch_utils/item_template_creation_utils.py

import json
import asyncio
from typing import List, Dict, Any, Optional

# --- Логгер ---
from game_server.services.logging.logging_setup import logger

# --- ИМПОРТЫ ДЛЯ ITEM_GENERATION_LOGIC ---
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_reader import ReferenceDataReader 
# 🔥 ИЗМЕНЕНИЕ: УДАЛЕН импорт CentralRedisClient, так как он больше не нужен здесь 🔥
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# 🔥 УДАЛЯЕМ ИМПОРТ parse_item_code, т.к. он больше не нужен 🔥
# from game_server.Logic.ApplicationLogic.coordinator_generator.utils.generator_utils import parse_item_code


class ItemGenerationLogic:
    """Содержит атомарную логику для генерации одного шаблона предмета."""
    
    # 🔥 ИЗМЕНЕНИЕ: Удален redis_client из конструктора 🔥
    def __init__(self):
        self._is_data_loaded = False
        self._item_base_data: Dict[str, Any] = {}
        self._materials_data: Dict[str, Any] = {}
        self._suffixes_data: Dict[str, Any] = {}
        self._modifiers_data: Dict[str, Any] = {}
        # 🔥 ИЗМЕНЕНИЕ: ReferenceDataReader теперь инициализируется без redis_client_instance 🔥
        self._reference_data_reader = ReferenceDataReader()

    async def _load_reference_data_from_redis(self):
        """
        Загружает все справочные данные, используя ReferenceDataReader,
        и СОХРАНЯЕТ их в атрибуты экземпляра.
        """
        if self._is_data_loaded:
            return

        logger.info("ItemGenerationLogic: Загрузка справочных данных из Redis...")
        
        results = await asyncio.gather(
            self._reference_data_reader.get_all_item_bases(),
            self._reference_data_reader.get_all_materials(),
            self._reference_data_reader.get_all_suffixes(),
            self._reference_data_reader.get_all_modifiers()
        )
        
        self._item_base_data, self._materials_data, self._suffixes_data, self._modifiers_data = results
        
        self._is_data_loaded = True
        logger.info("ItemGenerationLogic: Все справочные данные успешно загружены.")
        
    def _calculate_base_modifiers(self, item_base: Dict, material: Dict, suffix: Dict, rarity: int) -> Dict:
        """Выполняет расчет поля `base_modifiers_json`."""
        return {"placeholder": True}

    def _generate_display_name(self, item_base: Dict, material: Dict, suffix: Dict, specific_name: str, rarity: int) -> str:
        """Собирает читаемое имя предмета."""
        rarity_prefix = f"[T{rarity}]"
        material_adjective = material.get('adjective', '')
        suffix_fragment = suffix.get('fragment', '')
        return f"{rarity_prefix} {material_adjective} {specific_name} {suffix_fragment}".strip().replace('  ', ' ')

    # 🔥 ИСПРАВЛЕНИЕ: generate_single_template теперь принимает spec (словарь), а не item_code (строку) 🔥
    async def generate_single_template(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерирует полный словарь данных для одного шаблона предмета на основе полученной спецификации.
        """
        await self._load_reference_data_from_redis()

        # 🔥 УДАЛЕНО: Больше не парсим item_code, используем данные из spec 🔥
        # parts = parse_item_code(item_code)
        # if not parts:
        #     logger.error(f"Не удалось разобрать item_code: {item_code}")
        #     return None

        # Получаем данные напрямую из переданного словаря спецификации (spec)
        item_code = spec.get('item_code')
        category = spec.get('category')
        base_code = spec.get('base_code')
        specific_name_key = spec.get('specific_name_key')
        material_code = spec.get('material_code')
        suffix_code = spec.get('suffix_code')
        rarity = spec.get('rarity_level')

        # Проверка наличия ключевых полей из spec
        if not all([item_code, category, base_code, specific_name_key, material_code, suffix_code, rarity]):
            logger.error(f"Недостаточно данных в спецификации для генерации шаблона: {spec}")
            return None
        
        # Получаем полные данные из справочников по их кодам
        item_base = self._item_base_data.get(base_code)
        material = self._materials_data.get(material_code)
        suffix = self._suffixes_data.get(suffix_code)
        
        # 🔥 ИСПРАВЛЕНИЕ: Проверяем, что необходимые справочные данные найдены 🔥
        if not all([item_base, material, suffix]):
            logger.error(f"Не найдены все справочные компоненты для item_code: {item_code}. Проверьте данные в Redis для {base_code}, {material_code}, {suffix_code}.")
            return None

        # Преобразуем specific_name_key в формат, используемый для отображаемого имени
        # (предполагая, что specific_name_key может содержать пробелы или быть в другом регистре, если нужно)
        # Если specific_name_key уже готов к использованию в display_name, можно использовать напрямую
        specific_name_for_display = specific_name_key.replace('-', ' ') # Осталось, если specific_name_key из Planner имеет дефисы

        base_modifiers = self._calculate_base_modifiers(item_base, material, suffix, rarity)
        display_name = self._generate_display_name(item_base, material, suffix, specific_name_for_display, rarity)
        
        template_data = {
            "item_code": item_code,
            "display_name": display_name,
            "category": category, # Берем напрямую из spec
            "sub_category": base_code, # Берем напрямую из spec
            "equip_slot": item_base.get('properties', {}).get('equip_slot'), # Из справочника item_base
            "inventory_size": item_base.get('properties', {}).get('inventory_size'), # Из справочника item_base
            "material_code": material_code, # Берем напрямую из spec
            "suffix_code": suffix_code, # Берем напрямую из spec
            "rarity_level": rarity, # Берем напрямую из spec
            "base_modifiers_json": base_modifiers,
        }
        return template_data


# 🔥 ИЗМЕНЕНИЕ: generate_item_templates_from_specs больше не принимает redis_client 🔥
async def generate_item_templates_from_specs(
    batch_specs: List[Dict[str, Any]],
    log_prefix: str,
    # 🔥 УДАЛЕН redis_client из аргументов 🔥
    # redis_client: CentralRedisClient
) -> List[Dict[str, Any]]:
    """
    Генерирует полные шаблоны предметов из списка спецификаций.
    Эта функция является единственной точкой входа в данном модуле.
    Она использует `ItemGenerationLogic`, который самостоятельно загружает все
    необходимые справочные данные через `reference_data_reader` (который теперь использует глобальный клиент Redis).
    """
    if not batch_specs:
        logger.warning(f"{log_prefix} Получен пустой список спецификаций. Генерация не требуется.")
        return []

    # 🔥 ИЗМЕНЕНИЕ: ItemGenerationLogic теперь инициализируется без redis_client 🔥
    logic = ItemGenerationLogic() 
    
    generated_templates: List[Dict[str, Any]] = []
    
    for spec in batch_specs: # Итерируем по каждому словарю спецификаций
        # 🔥 ИСПРАВЛЕНИЕ: Передаем весь словарь spec в generate_single_template 🔥
        template = await logic.generate_single_template(spec)
        
        if template:
            generated_templates.append(template)
            
    logger.info(f"{log_prefix} Успешно сгенерировано {len(generated_templates)} шаблонов предметов.")
    return generated_templates
