# game_server\config\constants\redis.py

# ======================================================================
# --- ОБЩИЕ КОНСТАНТЫ REDIS ---
# ======================================================================

# --- Префиксы ключей для еще не отрефакторенных или глобальных модулей ---
# (Оставлен для будущего AccountCacheManager)
KEY_PREFIX_ACCOUNT_BINDINGS = "account_binding"
KEY_PREFIX_GAME_WORLD_STATE = "game_world"
KEY_PREFIX_GLOBAL_EVENTS = "global_events"
KEY_PREFIX_LEADERBOARDS = "leaderboard"


# --- Каналы Pub/Sub и Streams (глобальные, для межсервисного общения) ---
PUB_SUB_CHANNEL_CHARACTER_UPDATE = "character_updates"
PUB_SUB_CHANNEL_GAME_WORLD_EVENT = "game_world_events"
PUB_SUB_CHANNEL_GLOBAL_MESSAGE = "global_messages"
PUB_SUB_CHANNEL_TASK_COMPLETED = "task_completed"
PUB_SUB_CHANNEL_TICK_ADVANCE = "tick_advance"
REDIS_COORDINATOR_CHANNEL = "coordinator_channel"
REDIS_ALERTS_CHANNEL = "alerts_channel"
REDIS_SYSTEM_CHANNEL = "system_channel"
AUTH_SERVICE_TASK_CHANNEL = "auth_service:tasks"


# ======================================================================
# --- ПРОЧИЕ КОНСТАНТЫ, НЕ ПЕРЕНЕСЕННЫЕ В МОДУЛИ ---
# ======================================================================

# --- Пути к YAML-файлам (в идеале, их стоит вынести в отдельный settings-файл) ---
ITEM_BASE_YAML_PATH: str = "game_server/Logic/ApplicationLogic/world_orchestrator/workers/load_kesh_database/data/item_base"
LOCATION_CONNECTIONS_YAML_PATH: str = "game_server/Logic/ApplicationLogic/world_orchestrator/workers/load_kesh_database/data/world"



# --- Ключи для кэширования эталонного пула предметов ---
# (Оставлены здесь до рефакторинга соответствующего менеджера)
REDIS_KEY_ETALON_ITEM_POOL: str = "etalon_pool:items"
REDIS_KEY_ETALON_ITEM_FINGERPRINT: str = "etalon_pool:items:fingerprint"