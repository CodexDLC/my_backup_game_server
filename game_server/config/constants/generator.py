# game_server\config\constants\generator.py



# --- Категории типов существ (для фильтрации в CreatureType) ---
CREATURE_TYPE_CATEGORY_RACE = "RACE"
CREATURE_TYPE_CATEGORY_MONSTER = "MONSTER"
CREATURE_TYPE_CATEGORY_ITEM = "ITEM"

# Список всех известных категорий для валидации
ALL_CREATURE_TYPE_CATEGORIES = [
    CREATURE_TYPE_CATEGORY_RACE,
    CREATURE_TYPE_CATEGORY_MONSTER,
    CREATURE_TYPE_CATEGORY_ITEM,
]

# --- Ключи для работы с JSONB полями ---
JSONB_VISUAL_TAGS_KEY = "visual_tags"

# --- Флаги статусов ---
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_PENDING = "pending"


