# game_server/common_contracts/start_orcestrator/dtos.py

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Tuple, Dict, Any, Optional, List
import uuid # Для полей UUID

# --- DTO для спецификации генерации предмета ---
class ItemGenerationSpec(BaseModel):
    """
    Pydantic модель для одной спецификации генерации предмета.
    Используется для типизации и валидации данных на этапе планирования.
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

# --- DTO для спецификации генерации персонажа ---
class CharacterGenerationSpec(BaseModel):
    """
    Pydantic модель для одной спецификации генерации персонажа.
    Используется для типизации и валидации данных на этапе планирования.
    """
    gender: str = Field(..., description="Пол персонажа (MALE/FEMALE)")
    quality_level: str = Field(..., description="Уровень качества персонажа (например, COMMON, RARE)")
    creature_type_id: int = Field(..., description="ID типа существа/расы персонажа") # int, не str

# --- DTO для ItemBase Data ---
class ItemBaseData(BaseModel):
    """
    Pydantic модель для данных ItemBase, загружаемых из YAML.
    Теперь корректно соответствует структуре, где верхний ключ YAML - это item_code.
    """
    # item_code: Это уникальный код самого предмета (например, "DAGGER", "SWORD")
    # Он соответствует ключу верхнего уровня в YAML, который становится значением этого поля.
    item_code: str = Field(..., description="Уникальный код базового предмета (ключ верхнего уровня в YAML)")

    category: str = Field(..., description="Основная категория предмета (например, WEAPON, ARMOR)")

    # sub_category_code: Делаем его опциональным, так как он отсутствует в предоставленных YAML-данных.
    # Если в будущем он появится, он будет загружен. Если нет - будет None.
    sub_category_code: Optional[str] = Field(None, description="Код подкатегории предмета (например, 'LIGHT_MELEE', если применимо)") # <--- ИЗМЕНЕНО

    names: Dict[str, Any] = Field(default_factory=dict, description="Словарь специфических имен и их свойств")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Свойства предмета (например, equip_slot, inventory_size)")

# --- DTO для Material Data ---
class MaterialData(BaseModel):
    """
    Pydantic модель для данных Material, загружаемых из YAML.
    Соответствует ORM-модели Material.
    """
    material_code: str = Field(..., description="Уникальный код материала")
    name: str = Field(..., description="Название материала")
    type: str = Field(..., description="Тип материала")
    material_category: str = Field(..., description="Категория материала")
    rarity_level: Optional[int] = Field(None, description="Уровень редкости материала") # Optional
    adjective: str = Field(..., description="Прилагательное для материала")
    color: str = Field(..., description="Цвет материала")
    is_fragile: bool = Field(..., description="Флаг хрупкости")
    strength_percentage: float = Field(..., description="Процент прочности")


# --- DTO для Suffix Data ---
class SuffixData(BaseModel):
    """
    Pydantic модель для данных Suffix, загружаемых из YAML.
    Соответствует ORM-модели Suffix.
    """
    suffix_code: str = Field(..., description="Уникальный код суффикса")
    fragment: str = Field(..., description="Фрагмент для названия")
    group: str = Field(..., description="Группа суффикса")
    modifiers: List[Dict[str, Any]] = Field(default_factory=list, description="Список модификаторов") # JSONB, список словарей


# --- DTO для других Seed-моделей (метаданды 0-го уровня) ---

class AbilityData(BaseModel):
    """
    Pydantic модель для данных Ability.
    Соответствует ORM-модели Ability. PK: ability_id (int), но key: ability_key (str, unique)
    """
    ability_key: str = Field(..., description="Уникальный ключ способности")
    name: str = Field(..., description="Название способности")
    description: Optional[str] = Field(None, description="Описание способности")
    ability_type: str = Field(..., description="Тип способности")
    required_skill_key: Optional[str] = Field(None, description="Ключ требуемого навыка")
    required_skill_level: int = Field(0, description="Требуемый уровень навыка")
    required_stats: Optional[Dict[str, Any]] = Field(None, description="Требуемые статы") # JSONB
    required_items: Optional[Dict[str, Any]] = Field(None, description="Требуемые предметы") # JSONB
    cost_type: Optional[str] = Field(None, description="Тип стоимости (мана, энергия и т.д.)")
    cost_amount: int = Field(0, description="Количество стоимости")
    cooldown_seconds: int = Field(0, description="Время восстановления в секундах")
    cast_time_ms: int = Field(0, description="Время каста в миллисекундах")
    effect_data: Optional[Dict[str, Any]] = Field(None, description="Данные эффекта") # JSONB
    animation_key: Optional[str] = Field(None, description="Ключ анимации")
    sfx_key: Optional[str] = Field(None, description="Ключ звукового эффекта")
    vfx_key: Optional[str] = Field(None, description="Ключ визуального эффекта")


class BackgroundStoryData(BaseModel):
    """
    Pydantic модель для данных BackgroundStory.
    Соответствует ORM-модели BackgroundStory. PK: story_id (int), но name (str, unique)
    """
    # Добавлен `story_id` как Optional, если он не передается из YAML, но есть в БД
    # Если `story_id` генерируется БД, то его не должно быть в YAML.
    # Если `story_id` в YAML и является `int`
    story_id: Optional[int] = Field(None, description="ID предыстории (если есть в YAML)") # <--- ДОБАВЛЕНО
    name: str = Field(..., description="Внутреннее имя/ключ предыстории")
    display_name: str = Field(..., description="Отображаемое имя предыстории")
    short_description: Optional[str] = Field(None, description="Короткое описание")
    stat_modifiers: Optional[Dict[str, Any]] = Field(None, description="Модификаторы статов")
    skill_affinities: Optional[Dict[str, Any]] = Field(None, description="Сродство к навыкам")
    initial_inventory_items: Optional[Dict[str, Any]] = Field(None, description="Начальные предметы инвентаря")

    # ИЗМЕНЕНО: Теперь эти поля ожидаются как List[Any] для соответствия YAML []
    starting_location_tags: List[Any] = Field(default_factory=list, description="Теги стартовой локации") # <--- ИЗМЕНЕНО
    lore_fragments: List[Any] = Field(default_factory=list, description="Фрагменты лора") # <--- ИЗМЕНЕНО
    potential_factions: List[Any] = Field(default_factory=list, description="Потенциальные фракции") # <--- ИЗМЕНЕНО

    rarity_weight: int = Field(100, description="Вес редкости")

class CreatureTypeData(BaseModel):
    """
    Pydantic модель для данных CreatureType.
    Соответствует ORM-модели CreatureType. PK: creature_type_id (int)
    """
    creature_type_id: int = Field(..., description="Уникальный ID типа существа")
    name: str = Field(..., description="Название типа существа")
    description: str = Field(..., description="Описание типа существа")
    category: str = Field(..., description="Категория существа (например, RACE, MONSTER)")
    subcategory: Optional[str] = Field(None, description="Подкатегория существа")
    visual_tags: Optional[Dict[str, Any]] = Field(None, description="Визуальные теги существа") # JSONB
    rarity_weight: int = Field(100, description="Вес редкости")
    is_playable: bool = Field(False, description="Является ли существом играбельной расой")


class ModifierLibraryData(BaseModel):
    """
    Pydantic модель для данных ModifierLibrary.
    Соответствует ORM-модели ModifierLibrary. PK: modifier_code (str)
    """
    modifier_code: str = Field(..., description="Уникальный код модификатора")
    name: str = Field(..., description="Название модификатора")
    effect_description: str = Field(..., description="Описание эффекта")
    value_tiers: Dict[str, Any] = Field(..., description="Уровни значений модификатора") # JSONB
    randomization_range: float = Field(..., description="Диапазон рандомизации")


class PersonalityData(BaseModel):
    """
    Pydantic модель для данных Personality.
    Соответствует ORM-модели Personality. PK: personality_id (int), но name (str, unique)
    """
    # Добавлен `personality_id` как Optional, если он не передается из YAML, но есть в БД
    personality_id: Optional[int] = Field(None, description="ID личности (если есть в YAML)")
    name: str = Field(..., description="Уникальное имя личности")
    description: Optional[str] = Field(None, description="Описание личности")
    personality_group: Optional[str] = Field(None, description="Группа личности")
    
    # ИЗМЕНЕНО: Теперь эти поля ожидаются как List[Any] для соответствия YAML []
    behavior_tags: List[Any] = Field(default_factory=list, description="Теги поведения")
    dialogue_modifiers: Optional[Dict[str, Any]] = Field(None, description="Модификаторы диалогов")
    combat_ai_directives: Optional[Dict[str, Any]] = Field(None, description="Директивы боевого AI")
    quest_interaction_preferences: Optional[Dict[str, Any]] = Field(None, description="Предпочтения взаимодействия с квестами")
    trait_associations: Optional[Dict[str, Any]] = Field(None, description="Ассоциации с чертами")
    applicable_game_roles: List[Any] = Field(default_factory=list, description="Применимые игровые роли") # ИЗМЕНЕНО
    
    rarity_weight: int = Field(100, description="Вес редкости")
    ai_priority_level: int = Field(50, description="Уровень приоритета AI")


class SkillData(BaseModel):
    """
    Pydantic модель для данных Skill.
    Соответствует ORM-модели Skills. PK: skill_key (str)
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
    # Они будут формироваться из category_tag/role_preference_tag в логике.


class CreatureTypeInitialSkillData(BaseModel):
    """
    Pydantic модель для данных CreatureTypeInitialSkill.
    Соответствует ORM-модели CreatureTypeInitialSkill. Композитный PK: creature_type_id (int), skill_key (str)
    """
    creature_type_id: int = Field(..., description="ID типа существа")
    skill_key: str = Field(..., description="Ключ навыка")
    initial_level: int = Field(0, description="Начальный уровень")


class StaticItemTemplateData(BaseModel):
    """
    Pydantic модель для данных StaticItemTemplate.
    Соответствует ORM-модели StaticItemTemplate. PK: template_id (int), но item_code (str, unique)
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
    properties_json: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные свойства") # JSONB


class EquipmentTemplateData(BaseModel):
    """
    Pydantic модель для данных EquipmentTemplate.
    Соответствует ORM-модели EquipmentTemplate. PK: template_id (int), но item_code (str, unique)
    """
    item_code: str = Field(..., description="Уникальный код предмета")
    display_name: str = Field(..., description="Отображаемое имя")
    category: str = Field(..., description="Категория предмета")
    sub_category: str = Field(..., description="Подкатегория предмета")
    equip_slot: str = Field(..., description="Слот экипировки")
    inventory_size: str = Field(..., description="Размер инвентаря")
    material_code: str = Field(..., description="Код материала")
    suffix_code: Optional[str] = Field(None, description="Код суффикса")
    base_modifiers_json: Dict[str, Any] = Field(default_factory=dict, description="Базовые модификаторы") # JSONB
    quality_tier: Optional[str] = Field(None, description="Уровень качества")
    rarity_level: int = Field(..., description="Уровень редкости")
    icon_url: Optional[str] = Field(None, description="URL иконки")
    description: Optional[str] = Field(None, description="Описание")

# --- DTO для Core Attributes ---
class CharacterBaseStatsData(BaseModel):
    """
    Pydantic модель для базовых статов персонажа.
    Соответствует полям в CharacterSpecial.
    """
    strength: Optional[int] = Field(None, description="Сила")
    perception: Optional[int] = Field(None, description="Восприятие")
    endurance: Optional[int] = Field(None, description="Выносливость")
    agility: Optional[int] = Field(None, description="Ловкость")
    intelligence: Optional[int] = Field(None, description="Интеллект")
    charisma: Optional[int] = Field(None, description="Харизма")
    luck: Optional[int] = Field(None, description="Удача")


class CharacterRoleInputData(BaseModel):
    """
    Pydantic модель для входных данных функции assign_roles_and_archetypes_to_character_batch.
    Содержит уровень качества и базовые статы.
    """
    quality_level: str
    base_stats: CharacterBaseStatsData


class CharacterWithRoleArchetypeData(CharacterRoleInputData):
    """
    Pydantic модель для выходных данных функции assign_roles_and_archetypes_to_character_batch.
    Включает выбранные роль и архетип.
    """
    selected_role_name: str = Field(..., description="Название выбранной роли")
    selected_archetype_name: str = Field(..., description="Название выбранного архетипа")


class CoreAttributesData(BaseModel):
    """
    Pydantic модель для объединенных основных атрибутов персонажа.
    Это выходной формат generate_core_attributes_for_single_character.
    """
    base_stats: CharacterBaseStatsData
    initial_role_name: str
    selected_archetype_name: str
    initial_skill_levels: Dict[str, int]


# --- DTO для данных играбельной расы (для передачи планировщику персонажей) ---
class PlayableRaceData(BaseModel):
    """
    Pydantic модель для данных играбельной расы, передаваемых планировщику персонажей.
    Включает основные свойства и начальные навыки.
    Соответствует CreatureTypeData + initial_skills.
    """
    creature_type_id: int = Field(..., description="Уникальный ID типа существа")
    name: str = Field(..., description="Название расы")
    category: str = Field(..., description="Категория существа (должна быть RACE)")
    subcategory: Optional[str] = Field(None, description="Подкатегория расы")
    is_playable: bool = Field(True, description="Является ли раса играбельной")
    rarity_weight: Optional[int] = Field(None, description="Вес редкости расы") # int, не float
    description: Optional[str] = Field(None, description="Описание расы")
    visual_tags: Optional[Dict[str, Any]] = Field(None, description="Визуальные теги расы")
    initial_skills: List[Dict[str, Any]] = Field([], description="Список начальных навыков (словари)")


# --- DTO для мета-атрибутов персонажа ---
class CharacterMetaAttributesData(BaseModel):
    """
    Pydantic модель для мета-атрибутов персонажа.
    """
    is_unique: bool = Field(..., description="Является ли персонаж уникальным")
    rarity_score: int = Field(..., description="Очки редкости персонажа")
    
class StateEntityData(BaseModel):
    """
    Pydantic модель для данных StateEntity.
    Соответствует ORM-модели StateEntity. PK: access_code (str)
    """
    access_code: str = Field(..., description="Уникальный код доступа сущности состояния")
    code_name: str = Field(..., description="Кодовое имя сущности состояния")
    ui_type: str = Field(..., description="Тип пользовательского интерфейса")
    description: str = Field(..., description="Описание сущности состояния")
    is_active: bool = Field(True, description="Активна ли сущность состояния")
    created_at: Optional[datetime] = Field(None, description="Время создания (UTC)")
    
    

class GameLocationData(BaseModel):
    """
    Pydantic DTO для валидации данных из YAML-файлов для модели GameLocation.
    """
    access_key: str
    skeleton_template_id: str
    location_type: str
    name: str
    description: Optional[str] = None
    parent_access_key: Optional[str] = None
    is_peaceful: bool = Field(default=False)
    visibility: str

class LocationConnectionData(BaseModel):
    """
    Pydantic модель для данных о связях между локациями, загружаемых из YAML.
    """
    # Используем alias для соответствия полю 'from' в YAML
    from_location: str = Field(..., alias='from', description="Ключ исходной локации")
    to_location: str = Field(..., alias='to', description="Ключ целевой локации")
    description: str = Field(..., description="Описание связи")
