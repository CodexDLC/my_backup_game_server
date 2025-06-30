import json
import asyncio
from typing import List, Dict, Any, Optional, Type # Добавлен Type

# --- Логгер ---
from game_server.config.logging.logging_setup import app_logger as logger

# --- ИМПОРТЫ ДЛЯ ITEM_GENERATION_LOGIC ---
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.common_contracts.dtos.orchestrator_dtos import ItemBaseData, ItemGenerationSpec, MaterialData, SuffixData

# ДОБАВЛЕНО: Импорт ItemGenerationSpec DTO и других DTO



class ItemGenerationLogic:
    """Содержит атомарную логику для генерации одного шаблона предмета."""
    
    def __init__(self, reference_data_reader: ReferenceDataReader):
        self._is_data_loaded = False
        # ИЗМЕНЕНО: Типизация атрибутов для хранения DTO объектов
        self._item_base_data: Dict[str, ItemBaseData] = {}
        self._materials_data: Dict[str, MaterialData] = {}
        self._suffixes_data: Dict[str, SuffixData] = {}
        self._modifiers_data: Dict[str, Any] = {} # Модификаторы могут быть словарями или DTO
        self.reference_data_reader = reference_data_reader

    async def _load_reference_data_from_redis(self):
        """
        Загружает все справочные данные, используя ReferenceDataReader,
        и СОХРАНЯЕТ их в атрибуты экземпляра (в виде DTO).
        """
        if self._is_data_loaded:
            return

        logger.info("ItemGenerationLogic: Загрузка справочных данных из Redis...")
        
        # Получаем сырые данные (словари) из Redis.
        # ReferenceDataReader.get_all_... методы возвращают Dict[str, Dict[str, Any]].
        raw_item_bases, raw_materials, raw_suffixes, raw_modifiers = await asyncio.gather(
            self.reference_data_reader.get_all_item_bases(),
            self.reference_data_reader.get_all_materials(),
            self.reference_data_reader.get_all_suffixes(),
            self.reference_data_reader.get_all_modifiers()
        )
        
        # ИСПРАВЛЕНО: Явно преобразуем сырые словари в DTO объекты.
        # Это необходимо, так как ReferenceDataReader возвращает словари,
        # а не готовые DTO, как предполагалось ранее.
        try:
            self._item_base_data = {k: ItemBaseData(**v) for k, v in raw_item_bases.items()}
            self._materials_data = {k: MaterialData(**v) for k, v in raw_materials.items()}
            self._suffixes_data = {k: SuffixData(**v) for k, v in raw_suffixes.items()}
            # _modifiers_data могут быть словарями, если нет ModifierData DTO, или если они не Pydantic модели.
            self._modifiers_data = raw_modifiers # Оставляем как есть, если это просто Dict[str, Any]
        except Exception as e:
            logger.critical(f"ItemGenerationLogic: Ошибка при преобразовании справочных данных в DTO: {e}", exc_info=True)
            # В случае ошибки преобразования, возможно, стоит очистить данные, чтобы избежать дальнейших ошибок
            self._item_base_data = {}
            self._materials_data = {}
            self._suffixes_data = {}
            self._modifiers_data = {}
            raise # Пробрасываем ошибку, чтобы остановить процесс

        self._is_data_loaded = True
        logger.info("ItemGenerationLogic: Все справочные данные успешно загружены (как DTO).")
        
    def _calculate_base_modifiers(self, item_base: ItemBaseData, material: MaterialData, suffix: SuffixData, rarity: int) -> Dict:
        """Выполняет расчет поля `base_modifiers_json`."""
        # Здесь будет логика расчета модификаторов
        return {"placeholder": True}

    def _generate_display_name(self, item_base: ItemBaseData, material: MaterialData, suffix: SuffixData, specific_name: str, rarity: int) -> str:
        """Собирает читаемое имя предмета."""
        from game_server.config.provider import config
        
        rarity_prefix = f"[T{rarity}]"
        # Доступ к полям DTO через атрибуты (теперь 'material' и 'suffix' гарантированно DTO)
        material_adjective = material.name
        suffix_fragment = suffix.fragment
        return f"{rarity_prefix} {material_adjective} {specific_name} {suffix_fragment}".strip().replace('  ', ' ')

    async def generate_single_template(self, spec: ItemGenerationSpec) -> Optional[Dict[str, Any]]:
        """
        Генерирует полный словарь данных для одного шаблона предмета на основе полученной спецификации (DTO).
        """
        await self._load_reference_data_from_redis()

        item_code = spec.item_code
        category = spec.category
        base_code = spec.base_code
        specific_name_key = spec.specific_name_key
        material_code = spec.material_code
        suffix_code = spec.suffix_code
        rarity = spec.rarity_level

        item_base: Optional[ItemBaseData] = self._item_base_data.get(base_code)
        material: Optional[MaterialData] = self._materials_data.get(material_code)
        suffix: Optional[SuffixData] = self._suffixes_data.get(suffix_code)
        
        if not all([item_base, material, suffix]):
            logger.error(f"Не найдены все справочные компоненты для item_code: {item_code}. Проверьте данные в Redis для {base_code}, {material_code}, {suffix_code}.")
            return None

        specific_name_for_display = specific_name_key.replace('-', ' ')

        base_modifiers = self._calculate_base_modifiers(item_base, material, suffix, rarity)
        display_name = self._generate_display_name(item_base, material, suffix, specific_name_for_display, rarity)
        
        template_data = {
            "item_code": item_code,
            "display_name": display_name,
            "category": category,
            "sub_category": base_code,
            # Доступ к свойствам DTO ItemBaseData
            "equip_slot": item_base.properties.get('equip_slot'),
            "inventory_size": item_base.properties.get('inventory_size'),
            "material_code": material_code,
            "suffix_code": suffix_code,
            "rarity_level": rarity,
            "base_modifiers_json": base_modifiers,
        }
        return template_data


async def generate_item_templates_from_specs(
    batch_specs: List[ItemGenerationSpec],
    log_prefix: str,
    reference_data_reader: ReferenceDataReader,
) -> List[Dict[str, Any]]:
    """
    Генерирует полные шаблоны предметов из списка спецификаций (DTO).
    """
    if not batch_specs:
        logger.warning(f"{log_prefix} Получен пустой список спецификаций. Генерация не требуется.")
        return []

    logic = ItemGenerationLogic(
        reference_data_reader=reference_data_reader
    )
    
    generated_templates: List[Dict[str, Any]] = []
    
    for spec in batch_specs:
        template = await logic.generate_single_template(spec)
        
        if template:
            generated_templates.append(template)
            
    logger.info(f"{log_prefix} Успешно сгенерировано {len(generated_templates)} шаблонов предметов.")
    return generated_templates
