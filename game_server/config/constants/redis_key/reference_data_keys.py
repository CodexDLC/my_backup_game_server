# game_server/config/constants/redis/reference_data_keys.py

# Общий префикс для всех справочных данных, используемых генераторами
GENERATOR_DATA_PREFIX = "generator_data"

# Ключи для справочных данных генераторов
REDIS_KEY_GENERATOR_ITEM_BASE: str = f"{GENERATOR_DATA_PREFIX}:item_base"
REDIS_KEY_GENERATOR_MATERIALS: str = f"{GENERATOR_DATA_PREFIX}:materials"
REDIS_KEY_GENERATOR_SUFFIXES: str = f"{GENERATOR_DATA_PREFIX}:suffixes"
REDIS_KEY_GENERATOR_MODIFIERS: str = f"{GENERATOR_DATA_PREFIX}:modifiers"
REDIS_KEY_GENERATOR_SKILLS: str = f"{GENERATOR_DATA_PREFIX}:skills"
REDIS_KEY_GENERATOR_BACKGROUND_STORIES: str = f"{GENERATOR_DATA_PREFIX}:background_stories"
REDIS_KEY_GENERATOR_PERSONALITIES: str = f"{GENERATOR_DATA_PREFIX}:personalities"

# Ключ для связей между локациями
REDIS_KEY_WORLD_CONNECTIONS: str = f"{GENERATOR_DATA_PREFIX}:world_connections"

# Ключ для правил инвентаря (я заметил, что он был захардкожен в коде)
REDIS_KEY_GENERATOR_INVENTORY_RULES: str = f"{GENERATOR_DATA_PREFIX}:inventory_rules"