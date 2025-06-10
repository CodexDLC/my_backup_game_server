# coordinator_tick/constant_tick.py

# Redis Channels
COORDINATOR_CHANNEL = "coordinator_channel" # Этот канал теперь может быть удален, если он нигде больше не используется.

# Permitted task types
# PERMITTED_TASK_TYPES = ["training", "exploration", "crafting"] 

# Default TTLs in seconds (for Redis keys)
BATCH_TASK_TTL_SECONDS = 3600  # 1 час
BATCH_REPORT_TTL_SECONDS = 600 # 10 минут

# NEW: Batching configuration
BATCH_SIZE = 100 # Количество инструкций в одном батче


ALLOWED_TICK_TASKS = frozenset([
    "training",
    "exploration",
    "crafting"
])

# Константы RabbitMQ очередей
RABBITMQ_QUEUE_TICK_WORKER = "tick_coordinator_worker_queue" # Очередь для воркеров тиков
# 🔥 НОВАЯ КОНСТАНТА: Очередь для команд Координатору 🔥
COORDINATOR_COMMAND_QUEUE = "tick_coordinator_command_queue" # Очередь для команд Координатору (например, от Watcher)

# Константа команды для Watcher
COMMAND_RUN_COLLECTOR = "run_collector" # Это должно быть в constant_tick.py или в отдельном файле констант команд