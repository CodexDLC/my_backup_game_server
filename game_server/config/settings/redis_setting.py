# game_server\config\settings\redis.py 

# --- TTL по умолчанию для Redis (в секундах) ---

DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE = 3600 * 24       # 24 часа
DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE = 3600 * 1.5   # 1.5 часа
DEFAULT_TTL_ITEM_INSTANCE_CACHE = 3600                # 1 час
DEFAULT_TTL_SESSION_TOKEN = 3600 * 8                  # 8 часов
DEFAULT_TTL_ACCOUNT_BINDING = 0                       # Бессрочно
DEFAULT_TTL_GLOBAL_CACHE = 300                        # 5 минут
DEFAULT_TTL_STATIC_REF_DATA = 3600 * 24 * 30        # 30 дней
DEFAULT_TTL_TASK_STATUS = 3600 * 24 * 7             # 7 дней
DEFAULT_TTL_TASK_QUEUE_ITEM = 3600 * 24               # 1 день
BATCH_TASK_TTL_SECONDS = 3600                         # 1 час
TICK_WORKER_BATCH_TTL_SECONDS: int = 7200             # 2 часа