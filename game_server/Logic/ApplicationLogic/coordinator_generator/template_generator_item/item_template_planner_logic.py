# game_server/Logic/ApplicationLogic/coordinator_generator/template_generator_item/item_template_planner_logic.py

import json
import asyncio
import re
import time 
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Импорты, которые нужны для перенесенной логики
from game_server.Logic.ApplicationLogic.coordinator_generator.utils.generator_utils import generate_item_code
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.ORM_equipment_templates import EquipmentTemplateRepository

# 🔥 ИЗМЕНЕНИЕ: Теперь импортируем наш готовый экземпляр-одиночку, а не класс
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_reader import reference_data_reader
# � ИЗМЕНЕНИЕ: Этот импорт больше не нужен
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.services.logging.logging_setup import logger

# Константа для уровня редкости по умолчанию/не рарного предмета
DEFAULT_RARITY_LEVEL = 9 

# Константа для правил совместимости типов предметов и материалов
MATERIAL_COMPATIBILITY_RULES = {
    "WEAPON": {
        "allowed_types": ["METAL", "WOOD", "BONE"],
        "disallowed_types": ["FABRIC", "LEATHER"]
    },
    "ARMOR": {
        "allowed_types": ["METAL", "LEATHER"], 
        "disallowed_types": ["FABRIC"]
    },
    "APPAREL": {
        "allowed_types": ["FABRIC", "LEATHER", "FUR"], 
        "disallowed_types": ["METAL"] 
    },
    "ACCESSORY": {
        "allowed_types": ["METAL", "FABRIC", "LEATHER", "GEM", "BONE", "WOOD"],
        "disallowed_types": [] 
    },
    "UNKNOWN_CATEGORY": { 
        "allowed_types": [], 
        "disallowed_types": ["METAL", "FABRIC", "LEATHER"] 
    }
}

class ItemTemplatePlannerLogic:
    # 🔥 ИЗМЕНЕНИЕ: Убираем redis_client из аргументов, он больше не нужен
    def __init__(
        self,
        async_session_factory: Callable[[], AsyncSession],
        item_generation_limit: Optional[int] = None
    ):
        self.async_session_factory = async_session_factory
        self.item_generation_limit = item_generation_limit
        # 🔥 ИЗМЕНЕНИЕ: Используем наш готовый глобальный экземпляр ридера.
        # Больше не нужно создавать его здесь.
        self._reference_data_reader = reference_data_reader


    async def load_reference_data_from_redis(self) -> tuple[Dict, Dict, Dict, Dict]:
        """Загрузка всех справочных данных через менеджер."""
        logger.debug("ItemTemplatePlannerLogic: Загрузка справочных данных из Redis...")

        item_base = await self._reference_data_reader.get_all_item_bases()
        materials = await self._reference_data_reader.get_all_materials()
        suffixes = await self._reference_data_reader.get_all_suffixes()
        modifiers = await self._reference_data_reader.get_all_modifiers()

        logger.debug(f"ItemTemplatePlannerLogic: Загружено {len(item_base)} item_base, {len(materials)} материалов, {len(suffixes)} суффиксов, {len(modifiers)} модификаторов.")
        return item_base, materials, suffixes, modifiers

    async def get_existing_item_codes_from_db(self) -> Set[str]:
        """Получение существующих item_code из БД."""
        async with self.async_session_factory() as session:
            repo = EquipmentTemplateRepository(session)
            existing_codes = await repo.get_all_item_codes()
            logger.debug(f"ItemTemplatePlannerLogic: Получено {len(existing_codes)} существующих item_code из БД.")
            return set(existing_codes)

    def build_etalon_item_codes(
        self, item_base_data: Dict[str, Any], materials_data: Dict[str, Any], suffixes_data: Dict[str, Any]
    ) -> Dict[str, Tuple]:
        """Построение эталонного пула item_code и связанных данных."""
        # Используем словарь, чтобы гарантировать уникальность по item_code
        etalon_item_data_specs: Dict[str, Tuple] = {}
        logger.info("ItemTemplatePlannerLogic: Начало формирования эталонного пула item_code.")
        
        start_time = time.time()

        if not item_base_data or not materials_data or not suffixes_data:
            logger.warning("build_etalon_item_codes: Один или несколько наборов справочных данных пусты. Эталонный пул не будет построен.")
            return etalon_item_data_specs

        base_codes_processed = 0
        specific_names_processed = 0
        material_codes_processed = 0
        suffix_codes_processed = 0
        
        for base_code, base_info in item_base_data.items():
            base_codes_processed += 1
            category = base_info.get('category', 'UNKNOWN_CATEGORY') 
            specific_names_map = base_info.get('names', {})
            
            if not specific_names_map:
                logger.warning(f"build_etalon_item_codes: item_base '{base_code}' не имеет 'names' или они пусты. Пропускаем.")
                continue

            for original_specific_name, name_properties in specific_names_map.items():
                specific_names_processed += 1
                allowed_suffix_groups = set(name_properties.get('allowed_suffix_groups', []))
                
                if not allowed_suffix_groups and "BASIC_EMPTY" not in suffixes_data:
                    logger.warning(f"build_etalon_item_codes: specific_name '{original_specific_name}' для base '{base_code}' не имеет разрешенных групп суффиксов, и BASIC_EMPTY отсутствует. Пропускаем эту ветку.")

                for material_code, material_info in materials_data.items():
                    material_codes_processed += 1
                    
                    material_rarity_level = material_info.get('rarity_level') 

                    if material_rarity_level is None:
                        rarity_level_to_use = DEFAULT_RARITY_LEVEL
                        logger.debug(f"build_etalon_item_codes: Материал '{material_code}' не имеет 'rarity_level'. Используем уровень редкости по умолчанию: {DEFAULT_RARITY_LEVEL}.")
                    else:
                        rarity_level_to_use = int(material_rarity_level)
                    
                    material_type = material_info.get('type')
                    if not material_type:
                        logger.warning(f"build_etalon_item_codes: Материал '{material_code}' не имеет 'type'. Пропускаем.")
                        continue

                    is_compatible = False
                    category_rules = MATERIAL_COMPATIBILITY_RULES.get(category)
                    
                    if category_rules:
                        if material_type in category_rules.get("disallowed_types", []):
                            is_compatible = False
                        elif material_type in category_rules.get("allowed_types", []):
                            is_compatible = True
                        else:
                            is_compatible = False
                    else:
                        is_compatible = False

                    if not is_compatible:
                        logger.debug(f"build_etalon_item_codes: Несовместимая комбинация: Предмет '{category}' ({base_code}) и Материал '{material_type}' ({material_code}). Пропускаем.")
                        continue

                    suffix_codes_to_check = list(suffixes_data.keys())
                    if "BASIC_EMPTY" not in suffix_codes_to_check:
                        suffix_codes_to_check.insert(0, "BASIC_EMPTY")
                    
                    if not suffix_codes_to_check:
                        logger.warning(f"build_etalon_item_codes: Нет суффиксов для проверки. Пропускаем комбинацию с материалом '{material_code}'.")
                        continue

                    for suffix_code in suffix_codes_to_check:
                        suffix_codes_processed += 1
                        suffix_info = suffixes_data.get(suffix_code)
                        
                        is_suffix_allowed = (suffix_code == "BASIC_EMPTY" or 
                                             (suffix_info and suffix_info.get('group') and suffix_info.get('group') in allowed_suffix_groups))
                        
                        if not is_suffix_allowed:
                            logger.debug(f"build_etalon_item_codes: Суффикс '{suffix_code}' (группа: {suffix_info.get('group') if suffix_info else 'N/A'}) не разрешен для '{original_specific_name}' (разрешенные: {allowed_suffix_groups}). Пропускаем.")
                            continue

                        specific_name_for_code = re.sub(r'[^A-Z0-9]+', '-', original_specific_name).strip('-').upper()
                        
                        item_code = generate_item_code(
                            category=category, 
                            base_code=base_code, 
                            specific_name=specific_name_for_code,
                            material_code=material_code, 
                            suffix_code=suffix_code, 
                            rarity_level=rarity_level_to_use 
                        )
                        
                        spec_tuple = (
                            item_code, category, base_code, original_specific_name,
                            material_code, suffix_code, rarity_level_to_use
                        )
                        # Запись в словарь по уникальному item_code
                        etalon_item_data_specs[item_code] = spec_tuple

        end_time = time.time()
        elapsed_time = end_time - start_time 

        logger.info(f"build_etalon_item_codes: Процесс завершен. Обработано: "
                    f"bases={base_codes_processed}, specific_names={specific_names_processed}, "
                    f"materials={material_codes_processed}, suffixes={suffix_codes_processed}.")
        logger.info(f"ItemTemplatePlannerLogic: Построен эталонный пул из {len(etalon_item_data_specs)} уникальных item_code со связанными данными. Время выполнения: {elapsed_time:.2f} секунд.") 
        return etalon_item_data_specs

    def find_missing_specs(self, etalon_specs: Dict[str, Tuple], existing_codes: Set[str]) -> List[Tuple]:
        # Работаем со словарем
        missing_specs = [spec for item_code, spec in etalon_specs.items() if item_code not in existing_codes]
        return missing_specs

    def prepare_tasks_for_missing_items( 
        self, missing_specs: List[Tuple], item_generation_limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Подготовка задач для недостающих предметов с учетом лимита."""
        tasks_list: List[Dict[str, Any]] = []
        for item_code, category, base_code, specific_name_key, material_code, suffix_code, rarity_level in missing_specs:
            tasks_list.append({
                'item_code': item_code, 'category': category, 'base_code': base_code,
                'specific_name_key': specific_name_key, 'material_code': material_code,
                'suffix_code': suffix_code, 'rarity_level': rarity_level
            })
        if self.item_generation_limit is not None and self.item_generation_limit >= 0: 
            original_count = len(tasks_list)
            tasks_list = tasks_list[:self.item_generation_limit]
            if len(tasks_list) < original_count:
                logger.warning(f"item_template_planner_logic: Количество задач ограничено до {self.item_generation_limit} (изначально {original_count}).")
        return tasks_list
