# game_server/Logic/InfrastructureLogic/Generators/coordinator_generator/constant/constant_generator.py

"""
Модуль для хранения общих констант, используемых генераторами шаблонов и их координатором.
Эти константы помогают избежать "магических строк" и централизовать
ключевые значения, которые влияют на логику *процесса генерации шаблонов*.
"""
from typing import Dict, Any, List, Set # Добавлен импорт Set

# --- Категории типов существ (соответствуют полю 'category' в CreatureType) ---
# Используются для фильтрации данных из базы данных в оркестраторе и процессорах.
CREATURE_TYPE_CATEGORY_RACE = "RACE"
CREATURE_TYPE_CATEGORY_MONSTER = "MONSTER"
CREATURE_TYPE_CATEGORY_ITEM = "ITEM"
# Если будут другие категории, добавьте их здесь (например, CREATURE_TYPE_CATEGORY_ANIMAL = "ЖИВОТНОЕ")

# Список всех известных категорий для валидации или итерации, если это необходимо координатору.
ALL_CREATURE_TYPE_CATEGORIES = [
    CREATURE_TYPE_CATEGORY_RACE,
    CREATURE_TYPE_CATEGORY_MONSTER,
    CREATURE_TYPE_CATEGORY_ITEM,
]

# --- Ключи для работы с JSONB полями (если используются в логике фильтрации/обработки) ---
JSONB_VISUAL_TAGS_KEY = "visual_tags" # Ключ для доступа к визуальным тегам в данных CreatureType.

# --- Флаги статусов (если они используются в логике координации или генерации шаблонов) ---
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_PENDING = "pending"

# ======================================================================
# --- КОНСТАНТЫ ДЛЯ ГЕНЕРАТОРА ПЕРСОНАЖЕЙ (Перенесены из generator_settings.py) ---
# ======================================================================

# Имя очереди Celery для задач по генерации персонажей.
CHARACTER_GENERATION_WORKER_QUEUE_NAME: str = "character_generation_worker_queue"
# Шаблон ключа Redis для хранения данных батчей задач по генерации персонажей.
CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE: str = "generation_task:character:{batch_id}"
# Название уровня качества, считающегося наивысшим. Используется для логики распределения.
HIGHEST_QUALITY_LEVEL_NAME: str = "SUPERIOR_ELITE_QUALITY"

# --- Ключи Redis для справочных данных CharacterGenerator ---
# Ключи для данных, закэшированных в Redis для использования генератором персонажей.
REDIS_KEY_REF_PERSONALITIES: str = "ref_data:personalities"
REDIS_KEY_REF_BACKGROUND_STORIES: str = "ref_data:background_stories"
REDIS_KEY_REF_INVENTORY_RULES: str = "ref_data:inventory_rules"
REDIS_KEY_REF_VISUAL_TEMPLATES: str = "ref_data:visual_templates"
REDIS_KEY_REF_SKILLS: str = "ref_data:skills"

# --- ID по умолчанию для атрибутов персонажа ---
# Дефолтные ID для различных компонентов персонажа, если они не указаны явно.
DEFAULT_PERSONALITY_ID: int = 1
DEFAULT_BACKGROUND_STORY_ID: int = 1
DEFAULT_STARTER_INVENTORY_ID: int = 100

