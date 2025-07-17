# contracts/dtos/orchestrator/data_models.py

import uuid # Для uuid.UUID
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, List, Union

from pydantic import BaseModel, ConfigDict, Field

# Импортируем StateEntityDTO из dtos/state_entity/data_models (будет создана позже)
# from game_server.contracts.dtos.state_entity.data_models import StateEntityDTO # Пока закомментировано


class ItemGenerationSpec(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для одной спецификации генерации предмета.
    Используется для типизации и валидации данных на этапе планирования.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    item_code: str = Field(..., description="Уникальный код предмета")
    category: str = Field(..., description="Категория предмета")
    base_code: str = Field(..., description="Базовый код предмета")
    specific_name_key: str = Field(..., description="Ключ специфического имени (оригинальное имя из конфига)")
    material_code: str = Field(..., description="Код материала")
    suffix_code: Optional[str] = Field(None, description="Код суффикса") # NULLABLE
    rarity_level: int = Field(..., description="Уровень редкости")

    @classmethod
    def from_tuple(cls, s: Tuple) -> 'ItemGenerationSpec':
        """
        Фабричный метод для создания экземпляра ItemGenerationSpec из кортежа.
        Полезно для обратной совместимости или парсинга существующих кортежей.
        """
        if not (isinstance(s, tuple) and len(s) == 7):
            raise ValueError(f"Ожидается кортеж из 7 элементов, получено: {s}")
        return cls(
            item_code=s[0],
            category=s[1],
            base_code=s[2],
            specific_name_key=s[3],
            material_code=s[4],
            suffix_code=s[5],
            rarity_level=s[6]
        )

class CharacterGenerationSpec(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для одной спецификации генерации персонажа.
    Используется для типизации и валидации данных на этапе планирования.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    gender: str = Field(..., description="Пол персонажа (MALE/FEMALE)")
    quality_level: str = Field(..., description="Уровень качества персонажа (например, COMMON, RARE)")
    creature_type_id: int = Field(..., description="ID типа существа/расы персонажа") # int, не str

class ItemBaseData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных ItemBase, загружаемых из YAML.
    Теперь корректно соответствует структуре, где верхний ключ YAML - это item_code.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    item_code: str = Field(..., description="Уникальный код базового предмета (ключ верхнего уровня в YAML)")
    category: str = Field(..., description="Основная категория предмета (например, WEAPON, ARMOR)")
    sub_category_code: Optional[str] = Field(None, description="Код подкатегории предмета (например, 'LIGHT_MELEE', если применимо)")
    names: Dict[str, Any] = Field(default_factory=dict, description="Словарь специфических имен и их свойств")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Свойства предмета (например, equip_slot, inventory_size)")

class MaterialData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных Material, загружаемых из YAML.
    Соответствует ORM-модели Material.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    material_code: str = Field(..., description="Уникальный код материала")
    name: str = Field(..., description="Название материала")
    type: str = Field(..., description="Тип материала")
    material_category: str = Field(..., description="Категория материала")
    rarity_level: Optional[int] = Field(None, description="Уровень редкости материала")
    adjective: str = Field(..., description="Прилагательное для материала")
    color: str = Field(..., description="Цвет материала")
    is_fragile: bool = Field(..., description="Флаг хрупкости")
    strength_percentage: float = Field(..., description="Процент прочности")


class SuffixData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных Suffix, загружаемых из YAML.
    Соответствует ORM-модели Suffix.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    suffix_code: str = Field(..., description="Уникальный код суффикса")
    fragment: str = Field(..., description="Фрагмент для названия")
    group: str = Field(..., description="Группа суффикса")
    modifiers: List[Dict[str, Any]] = Field(default_factory=list, description="Список модификаторов")


# --- DTO для других Seed-моделей (метаданды 0-го уровня) ---

class AbilityData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных Ability.
    Соответствует ORM-модели Ability.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    ability_key: str = Field(..., description="Уникальный ключ способности")
    name: str = Field(..., description="Название способности")
    description: Optional[str] = Field(None, description="Описание способности")
    ability_type: str = Field(..., description="Тип способности")
    required_skill_key: Optional[str] = Field(None, description="Ключ требуемого навыка")
    required_skill_level: int = Field(0, description="Требуемый уровень навыка")
    required_stats: Optional[Dict[str, Any]] = Field(None, description="Требуемые статы")
    required_items: Optional[Dict[str, Any]] = Field(None, description="Требуемые предметы")
    cost_type: Optional[str] = Field(None, description="Тип стоимости (мана, энергия и т.д.)")
    cost_amount: int = Field(0, description="Количество стоимости")
    cooldown_seconds: int = Field(0, description="Время восстановления в секундах")
    cast_time_ms: int = Field(0, description="Время каста в миллисекундах")
    effect_data: Optional[Dict[str, Any]] = Field(None, description="Данные эффекта")
    animation_key: Optional[str] = Field(None, description="Ключ анимации")
    sfx_key: Optional[str] = Field(None, description="Ключ звукового эффекта")
    vfx_key: Optional[str] = Field(None, description="Ключ визуального эффекта")


class BackgroundStoryData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных BackgroundStory.
    Соответствует ORM-модели BackgroundStory.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    story_id: Optional[int] = Field(None, description="ID предыстории (если есть в YAML)")
    name: str = Field(..., description="Внутреннее имя/ключ предыстории")
    display_name: str = Field(..., description="Отображаемое имя предыстории")
    short_description: Optional[str] = Field(None, description="Короткое описание")
    stat_modifiers: Optional[Dict[str, Any]] = Field(None, description="Модификаторы статов")
    skill_affinities: Optional[Dict[str, Any]] = Field(None, description="Сродство к навыкам")
    initial_inventory_items: Optional[Dict[str, Any]] = Field(None, description="Начальные предметы инвентаря")
    starting_location_tags: List[Any] = Field(default_factory=list, description="Теги стартовой локации")
    lore_fragments: List[Any] = Field(default_factory=list, description="Фрагменты лора")
    potential_factions: List[Any] = Field(default_factory=list, description="Потенциальные фракции")
    rarity_weight: int = Field(100, description="Вес редкости")
    ai_priority_level: int = Field(50, description="Уровень приоритета AI")


class CreatureTypeData(BaseModel):
    """
    Pydantic модель для данных CreatureType.
    Соответствует ORM-модели CreatureType.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    creature_type_id: int = Field(..., description="Уникальный ID типа существа")
    name: str = Field(..., description="Название типа существа")
    description: str = Field(..., description="Описание типа существа")
    category: str = Field(..., description="Категория существа (например, RACE, MONSTER)")
    subcategory: Optional[str] = Field(None, description="Подкатегория существа")
    visual_tags: Optional[Dict[str, Any]] = Field(None, description="Визуальные теги существа")
    rarity_weight: int = Field(100, description="Вес редкости")
    is_playable: bool = Field(False, description="Является ли существом играбельной расы")

    # 👇 ДОБАВЬТЕ ЭТУ СТРОЧКУ В КОНЕЦ КЛАССА
    model_config = ConfigDict(from_attributes=True)


class ModifierLibraryData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных ModifierLibrary.
    Соответствует ORM-модели ModifierLibrary.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    modifier_code: str = Field(..., description="Уникальный код модификатора")
    name: str = Field(..., description="Название модификатора")
    effect_description: str = Field(..., description="Описание эффекта")
    value_tiers: Dict[str, Any] = Field(..., description="Уровни значений модификатора")
    randomization_range: float = Field(..., description="Диапазон рандомизации")


class PersonalityData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных Personality.
    Соответствует ORM-модели Personality.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    personality_id: Optional[int] = Field(None, description="ID личности (если есть в YAML)")
    name: str = Field(..., description="Уникальное имя личности")
    description: Optional[str] = Field(None, description="Описание личности")
    personality_group: Optional[str] = Field(None, description="Группа личности")
    behavior_tags: List[Any] = Field(default_factory=list, description="Теги поведения")
    dialogue_modifiers: Optional[Dict[str, Any]] = Field(None, description="Модификаторы диалогов")
    combat_ai_directives: Optional[Dict[str, Any]] = Field(None, description="Директивы боевого AI")
    quest_interaction_preferences: Optional[Dict[str, Any]] = Field(None, description="Предпочтения взаимодействия с квестами")
    trait_associations: Optional[Dict[str, Any]] = Field(None, description="Ассоциации с чертами")
    applicable_game_roles: List[Any] = Field(default_factory=list, description="Применимые игровые роли")
    rarity_weight: int = Field(100, description="Вес редкости")
    ai_priority_level: int = Field(50, description="Уровень приоритета AI")


class SkillData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных Skill.
    Соответствует ORM-модели Skills.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    skill_key: str = Field(..., description="Уникальный ключ навыка")
    name: str = Field(..., description="Название навыка")
    description: Optional[str] = Field(None, description="Описание навыка")
    stat_influence: Dict[str, Any] = Field(..., description="Влияние на статы")
    is_magic: bool = Field(False, description="Является ли магическим")
    rarity_weight: int = Field(100, description="Вес редкости")
    category_tag: str = Field(..., description="Категория тега навыка")
    role_preference_tag: Optional[str] = Field(None, description="Тег предпочтения роли")
    limit_group_tag: Optional[str] = Field(None, description="Тег группы ограничения")
    max_level: int = Field(1, description="Максимальный уровень")
    # УДАЛЕНО: categories: List[str] и tags: List[str] - они не являются прямыми полями модели Skills.


class CreatureTypeInitialSkillData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных CreatureTypeInitialSkill.
    Соответствует ORM-модели CreatureTypeInitialSkill.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    creature_type_id: int = Field(..., description="ID типа существа")
    skill_key: str = Field(..., description="Ключ навыка")
    initial_level: int = Field(0, description="Начальный уровень")


class StaticItemTemplateData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных StaticItemTemplate.
    Соответствует ORM-модели StaticItemTemplate.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    item_code: str = Field(..., description="Уникальный код предмета")
    display_name: str = Field(..., description="Отображаемое имя")
    category: str = Field(..., description="Категория предмета")
    sub_category: Optional[str] = Field(None, description="Подкатегория предмета")
    inventory_size: str = Field(..., description="Размер инвентаря")
    stackable: bool = Field(False, description="Можно ли стакать")
    max_stack_size: int = Field(1, description="Максимальный размер стака")
    base_value: int = Field(0, description="Базовая стоимость")
    icon_url: Optional[str] = Field(None, description="URL иконки")
    description: Optional[str] = Field(None, description="Описание")
    properties_json: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные свойства")


class EquipmentTemplateData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных EquipmentTemplate.
    Соответствует ORM-модели EquipmentTemplate.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    item_code: str = Field(..., description="Уникальный код предмета")
    display_name: str = Field(..., description="Отображаемое имя")
    category: str = Field(..., description="Категория предмета")
    sub_category: str = Field(..., description="Подкатегория предмета")
    equip_slot: str = Field(..., description="Слот экипировки")
    inventory_size: str = Field(..., description="Размер инвентаря")
    material_code: str = Field(..., description="Код материала")
    suffix_code: Optional[str] = Field(None, description="Код суффикса")
    base_modifiers_json: Dict[str, Any] = Field(default_factory=dict, description="Базовые модификаторы")
    quality_tier: Optional[str] = Field(None, description="Уровень качества")
    rarity_level: int = Field(..., description="Уровень редкости")
    icon_url: Optional[str] = Field(None, description="URL иконки")
    description: Optional[str] = Field(None, description="Описание")

# --- DTO для Core Attributes ---
class CharacterBaseStatsData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для базовых статов персонажа.
    Соответствует полям в CharacterSpecial.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    strength: Optional[int] = Field(None, description="Сила")
    perception: Optional[int] = Field(None, description="Восприятие")
    endurance: Optional[int] = Field(None, description="Выносливость")
    agility: Optional[int] = Field(None, description="Ловкость")
    intelligence: Optional[int] = Field(None, description="Интеллект")
    charisma: Optional[int] = Field(None, description="Харизма")
    luck: Optional[int] = Field(None, description="Удача")


class CharacterRoleInputData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для входных данных функции assign_roles_and_archetypes_to_character_batch.
    Содержит уровень качества и базовые статы.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    quality_level: str
    base_stats: CharacterBaseStatsData


class CharacterWithRoleArchetypeData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для выходных данных функции assign_roles_and_archetypes_to_character_batch.
    Включает выбранные роль и архетип.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    quality_level: str
    base_stats: CharacterBaseStatsData
    selected_role_name: str = Field(..., description="Название выбранной роли")
    selected_archetype_name: str = Field(..., description="Название выбранного архетипа")


class CoreAttributesData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для объединенных основных атрибутов персонажа.
    Это выходной формат generate_core_attributes_for_single_character.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    base_stats: CharacterBaseStatsData
    initial_role_name: str
    selected_archetype_name: str
    initial_skill_levels: Dict[str, int]


class PlayableRaceData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для данных играбельной расы, передаваемых планировщику персонажей.
    Включает основные свойства и начальные навыки.
    Соответствует CreatureTypeData + initial_skills.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    creature_type_id: int = Field(..., description="Уникальный ID типа существа")
    name: str = Field(..., description="Название расы")
    category: str = Field(..., description="Категория существа (должна быть RACE)")
    subcategory: Optional[str] = Field(None, description="Подкатегория расы")
    is_playable: bool = Field(True, description="Является ли раса играбельной")
    rarity_weight: Optional[int] = Field(None, description="Вес редкости расы")
    description: Optional[str] = Field(None, description="Описание расы")
    visual_tags: Optional[Dict[str, Any]] = Field(None, description="Визуальные теги расы")
    initial_skills: List[Dict[str, Any]] = Field([], description="Список начальных навыков (словари)")


class CharacterMetaAttributesData(BaseModel): # Наследуем от BaseModel
    """
    Pydantic модель для мета-атрибутов персонажа.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    is_unique: bool = Field(..., description="Является ли персонаж уникальным")
    rarity_score: int = Field(..., description="Очки редкости персонажа")

class LocationExitData(BaseModel):
    """
    Pydantic DTO для валидации структуры 'exits' в YAML-файлах.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    label: str
    target_location_id: str

class LocationPresentationData(BaseModel):
    """
    Pydantic DTO для валидации структуры 'presentation' в YAML-файлах.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    image_url: Optional[str] = None
    icon_emoji: Optional[str] = None

class GameLocationData(BaseModel):
    """
    Pydantic DTO для валидации данных о локации, загружаемых из YAML-файлов.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    access_key: str = Field(alias="location_id")
    skeleton_template_id: Optional[str] = None
    specific_category: str = Field(alias="location_type")
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = Field(alias="parent_access_key", default=None)
    is_peaceful: Optional[bool] = Field(default=None)
    visibility: Optional[str] = Field(None, description="Видимость локации (например, 'PUBLIC', 'PRIVATE').") # Добавлено описание
    exits: List[LocationExitData] = []
    child_location_ids: List[str] = []
    unified_display_type: Optional[str] = Field(None, description="Унифицированный тип отображения локации.") # Добавлено описание
    presentation: Optional[LocationPresentationData] = Field(None, description="Данные для презентации локации (изображение, иконка).") # Добавлено описание
    entry_point_location_id: Optional[str] = Field(None, description="ID локации, которая является точкой входа.") # Добавлено описание
    flavor_text_options: List[str] = []
    tags: List[str] = []
    class Config:
        populate_by_name = True
        extra = 'ignore'

class LocationConnectionData(BaseModel):
    """
    Pydantic модель для данных о связях между локациями, загружаемых из YAML.
    Перенесено из game_server/common_contracts/dtos/orchestrator_dtos.py
    """
    from_location: str = Field(alias='from', description="Ключ исходной локации")
    to_location: str = Field(alias='to', description="Ключ целевой локации")
    description: str = Field(..., description="Описание связи")

