# game_server/Logic/InfrastructureLogic/app_cache/central_redis_constants.py

# --- Префиксы ключей для центрального Redis ---
# Используются для организации данных в Redis по модулям/сущностям.
# Следуют концепции "ключи-папки, JSON-файлы".

# Ключи, связанные с персонажами (их актуальный слепок, привязки)
KEY_PREFIX_CHARACTER_SNAPSHOT = "character"           # Полный актуальный слепок персонажа (uuid)
KEY_PREFIX_ACCOUNT_BINDINGS = "account_binding"       # Связка Discord/Game Account ID с Character ID

# Ключи, связанные с предметами (экземпляры предметов, шаблоны)
KEY_PREFIX_ITEM_INSTANCE = "item_instance"            # Экземпляры предметов (uuid)

# Ключи, связанные с игровым миром и глобальными событиями
KEY_PREFIX_GAME_WORLD_STATE = "game_world"            # Глобальное состояние мира/инстансов
KEY_PREFIX_GLOBAL_EVENTS = "global_events"            # Общие события, новости, оповещения

# Ключи, связанные с задачами и очередями (для Celery, тиковой системы и статусов)
KEY_PREFIX_TASK_QUEUE = "task_queue"                  # Очереди задач (например, для Celery или тика)
KEY_PREFIX_TASK_STATUS = "task_status"                # Статусы выполнения отдельных задач
KEY_PREFIX_TICK_TASKS = "tick_tasks"                  # Специальная очередь для тиковых задач

# 🔥 ИЗМЕНЕНО: Общий префикс для всех статических справочных данных генераторов 🔥
GENERATOR_DATA_PREFIX = "generator_data"      # Новый унифицированный префикс

# 🔥 УДАЛЕНО: Эта константа больше не нужна, т.к. используется GENERATOR_DATA_PREFIX 🔥
# KEY_PREFIX_STATIC_REF_DATA = "static_ref_data"      # Шаблоны предметов, материалов, скиллов и т.д.

# Ключи для других систем
KEY_PREFIX_LEADERBOARDS = "leaderboard"               # Таблицы лидеров
KEY_PREFIX_SESSION_TOKENS = "session_token"           # Токены сессий REST API (для аутентификации)


# --- TTL по умолчанию для центрального Redis (в секундах) ---
# Эти значения будут импортированы из game_server/config/settings.py
# (туда их нужно будет добавить, если их там еще нет, и они будут браться из ENV)
DEFAULT_TTL_CHARACTER_SNAPSHOT_ONLINE = 3600 * 24     # 24 часа для активного персонажа (обновляется при активности)
DEFAULT_TTL_CHARACTER_SNAPSHOT_OFFLINE = 3600 * 1.5   # 1.5 часа для персонажа, который только что оффлайн (для быстрого возврата)
DEFAULT_TTL_ITEM_INSTANCE_CACHE = 3600                # 1 час для кэша экземпляров предметов (если не персистентны в БД)
DEFAULT_TTL_SESSION_TOKEN = 3600 * 8                  # 8 часов для сессионных токенов
DEFAULT_TTL_ACCOUNT_BINDING = 0                       # 0 = бессрочно, для персистентных связок Discord ID с Character ID
DEFAULT_TTL_GLOBAL_CACHE = 300                        # 5 минут для общего кэша (например, новости, данные, которые часто меняются)
DEFAULT_TTL_STATIC_REF_DATA = 3600 * 24 * 30          # 🔥 ИЗМЕНЕНО: 30 дней для статических справочных данных 🔥
DEFAULT_TTL_TASK_STATUS = 3600 * 24 * 7               # 7 дней для статуса задачи (пример)
DEFAULT_TTL_TASK_QUEUE_ITEM = 3600 * 24               # 24 часа для элемента в очереди (если не будет обработан быстрее)


# --- Каналы Pub/Sub для центрального Redis (если они не управляются Celery/RabbitMQ) ---
# Используются для асинхронных уведомлений внутри Backend'а между сервисами
PUB_SUB_CHANNEL_CHARACTER_UPDATE = "character_updates"       # Обновления состояния персонажа (для WebSocket пуша)
PUB_SUB_CHANNEL_GAME_WORLD_EVENT = "game_world_events"       # Глобальные события в игровом мире
PUB_SUB_CHANNEL_GLOBAL_MESSAGE = "global_messages"           # Общие сообщения для всех подключенных сервисов
PUB_SUB_CHANNEL_TASK_COMPLETED = "task_completed"            # Сигнал о завершении задачи
PUB_SUB_CHANNEL_TICK_ADVANCE = "tick_advance"                # Сигнал о продвижении игрового тика


# ======================================================================
# --- КОНСТАНТЫ ДЛЯ ГЕНЕРАТОРА ПРЕДМЕТОВ (Перенесены из generator_settings.py) ---
# ======================================================================

# --- Пути к данным ---
# Путь к директории с YAML-файлами, определяющими базовые архетипы предметов.
ITEM_BASE_YAML_PATH: str = "game_server/Logic/ApplicationLogic/coordinator_generator/data/item_base"

# 🔥 ИЗМЕНЕНО/НОВОЕ: Унифицированные ключи Redis для всех данных генератора (предметов и персонажей) 🔥
REDIS_KEY_GENERATOR_ITEM_BASE: str = f"{GENERATOR_DATA_PREFIX}:item_base" # item_data:base переименовывается
REDIS_KEY_GENERATOR_MATERIALS: str = f"{GENERATOR_DATA_PREFIX}:materials" # item_data:materials переименовывается
REDIS_KEY_GENERATOR_SUFFIXES: str = f"{GENERATOR_DATA_PREFIX}:suffixes" # item_data:suffixes переименовывается
REDIS_KEY_GENERATOR_MODIFIERS: str = f"{GENERATOR_DATA_PREFIX}:modifiers" # item_data:modifiers переименовывается

REDIS_KEY_GENERATOR_SKILLS: str = f"{GENERATOR_DATA_PREFIX}:skills" # static_ref_data:skills переименовывается
REDIS_KEY_GENERATOR_BACKGROUND_STORIES: str = f"{GENERATOR_DATA_PREFIX}:background_stories" # static_ref_data:background_stories переименовывается
REDIS_KEY_GENERATOR_PERSONALITIES: str = f"{GENERATOR_DATA_PREFIX}:personalities" # static_ref_data:personalities переименовывается
REDIS_KEY_GENERATOR_INVENTORY_RULES: str = f"{GENERATOR_DATA_PREFIX}:inventory_rules" # static_ref_data:inventory_rules переименовывается

# 🔥 УДАЛЕНО: Старые REDIS_KEY_ITEM_DATA_* больше не используются,
#             т.к. мы используем новый GENERATOR_DATA_PREFIX
# REDIS_KEY_ITEM_DATA_BASE: str = "item_data:base"
# REDIS_KEY_ITEM_DATA_MATERIALS: str = "item_data:materials"
# REDIS_KEY_ITEM_DATA_SUFFIXES: str = "item_data:suffixes"
# REDIS_KEY_ITEM_DATA_MODIFIERS: str = "item_data:modifiers"


# Имя очереди Celery для задач по генерации предметов.
ITEM_GENERATION_WORKER_QUEUE_NAME: str = "item_generation_worker_queue"
# Шаблон ключа Redis для хранения данных батчей задач по генерации предметов.
ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE: str = "generation_task:item:{batch_id}"
# Ключ Redis для общего списка задач генерации предметов (возможно, используется для мониторинга).
REDIS_KEY_ITEM_DATA_GENERATION_TASKS: str = "item_data:generation_tasks"


# ======================================================================
# --- НАСТРОЙКИ CELERY/RABBITMQ И REDIS TTL ---
# ======================================================================

# Время жизни сообщения в очереди RabbitMQ (в секундах).
# Если воркер не заберет сообщение за это время, RabbitMQ удалит его.
# CELERY_MESSAGE_EXPIRES_SECONDS: int = 7200 # 2 часа (3600 * 2) - Эту константу мы пока не используем.

# НОВАЯ КОНСТАНТА: Начальное время жизни ключа задачи в Redis (в секундах).
# Применяется при создании задачи. Задачи, не обработанные за это время, удалятся.
REDIS_TASK_INITIAL_TTL_SECONDS: int = 10800 # 3 часа (3600 * 3)

REDIS_COORDINATOR_TASK_HASH = "coordinator:tasks"
REDIS_TASK_QUEUE_EXPLORATION = "exploration"
REDIS_TASK_QUEUE_TRAINING = "training" 
REDIS_TASK_QUEUE_CRAFTING = "crafting"