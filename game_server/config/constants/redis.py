#  game_server\config\constants\redis.py

# ======================================================================
# --- ОБЩИЕ КОНСТАНТЫ REDIS ---
# ======================================================================

# --- Префиксы ключей ---
KEY_PREFIX_CHARACTER_SNAPSHOT = "character"
KEY_PREFIX_ACCOUNT_BINDINGS = "account_binding"
KEY_PREFIX_ITEM_INSTANCE = "item_instance"
KEY_PREFIX_GAME_WORLD_STATE = "game_world"
KEY_PREFIX_GLOBAL_EVENTS = "global_events"
KEY_PREFIX_TASK_QUEUE = "task_queue"
KEY_PREFIX_TASK_STATUS = "task_status"
KEY_PREFIX_TICK_TASKS = "tick_tasks"
GENERATOR_DATA_PREFIX = "generator_data"
KEY_PREFIX_LEADERBOARDS = "leaderboard"
KEY_PREFIX_SESSION_TOKENS = "session_token"

# --- Каналы Pub/Sub ---
PUB_SUB_CHANNEL_CHARACTER_UPDATE = "character_updates"
PUB_SUB_CHANNEL_GAME_WORLD_EVENT = "game_world_events"
PUB_SUB_CHANNEL_GLOBAL_MESSAGE = "global_messages"
PUB_SUB_CHANNEL_TASK_COMPLETED = "task_completed"
PUB_SUB_CHANNEL_TICK_ADVANCE = "tick_advance"
REDIS_COORDINATOR_CHANNEL = "coordinator_channel"
REDIS_ALERTS_CHANNEL = "alerts_channel"
REDIS_SYSTEM_CHANNEL = "system_channel"

# --- Очереди задач ---
REDIS_TASK_QUEUE_EXPLORATION = "exploration"
REDIS_TASK_QUEUE_TRAINING = "training"
REDIS_TASK_QUEUE_CRAFTING = "crafting"

# ======================================================================
# --- КОНСТАНТЫ ГЕНЕРАТОРОВ ---
# ======================================================================

# --- Пути к YAML-файлам для загрузчиков ---
ITEM_BASE_YAML_PATH: str = "game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/data/item_base"
LOCATION_CONNECTIONS_YAML_PATH: str = "game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/data/world"


# --- Ключи для справочных данных генераторов ---
REDIS_KEY_GENERATOR_ITEM_BASE: str = f"{GENERATOR_DATA_PREFIX}:item_base"
REDIS_KEY_GENERATOR_MATERIALS: str = f"{GENERATOR_DATA_PREFIX}:materials"
REDIS_KEY_GENERATOR_SUFFIXES: str = f"{GENERATOR_DATA_PREFIX}:suffixes"
REDIS_KEY_GENERATOR_MODIFIERS: str = f"{GENERATOR_DATA_PREFIX}:modifiers"
REDIS_KEY_GENERATOR_SKILLS: str = f"{GENERATOR_DATA_PREFIX}:skills"
REDIS_KEY_GENERATOR_BACKGROUND_STORIES: str = f"{GENERATOR_DATA_PREFIX}:background_stories"
REDIS_KEY_GENERATOR_PERSONALITIES: str = f"{GENERATOR_DATA_PREFIX}:personalities"

# --- НОВЫЙ КЛЮЧ ДЛЯ СВЯЗЕЙ МЕЖДУ ЛОКАЦИЯМИ ---
REDIS_KEY_WORLD_CONNECTIONS: str = f"{GENERATOR_DATA_PREFIX}:world_connections"

# --- Ключи и шаблоны для задач генерации ---
ITEM_GENERATION_WORKER_QUEUE_NAME: str = "item_generation_worker_queue"
ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE: str = "generation_task:item:{batch_id}"
REDIS_KEY_ITEM_DATA_GENERATION_TASKS: str = "item_data:generation_tasks"

# --- Ключи для кэширования эталонного пула предметов ---
REDIS_KEY_ETALON_ITEM_POOL: str = "etalon_pool:items"
REDIS_KEY_ETALON_ITEM_FINGERPRINT: str = "etalon_pool:items:fingerprint"


# ======================================================================
# --- КОНСТАНТЫ КООРДИНАТОРА ---
# ======================================================================

# --- Ключи и шаблоны для задач координатора ---
REDIS_COORDINATOR_TASK_HASH = "coordinator:tasks"
TICK_WORKER_BATCH_KEY_TEMPLATE: str = "tick_batch:{batch_id}"



# --- Генератор Персонажей ---
CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE: str = "generation_task:character:{batch_id}"


# --- Character Pool Constants ---
KEY_CHARACTER_POOL_AVAILABLE_COUNT = "characters:pool:available_count"


