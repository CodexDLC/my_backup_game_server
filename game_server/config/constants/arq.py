# game_server/config/constants/arq.py

# --- Пути к ARQ-задачам (для постановки задач через ArqTaskDispatcher) ---
ARQ_TASK_GENERATE_CHARACTER_BATCH: str = "game_server.Logic.ApplicationLogic.world_orchestrator.workers.tasks.arq_character_generation.generate_character_batch_task"
ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH: str = "game_server.Logic.ApplicationLogic.world_orchestrator.workers.tasks.arq_item_generation.process_item_generation_batch_task"
ARQ_TASK_GENERATE_WORLD_MAP: str = "game_server.Logic.ApplicationLogic.world_orchestrator.workers.tasks.arq_world_map_generation.generate_world_map_task"



# Список задач, которые может выполнять воркер (для arq_worker_settings.py)
TASKS = [
    ARQ_TASK_GENERATE_CHARACTER_BATCH,
    ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH,
    ARQ_TASK_GENERATE_WORLD_MAP,
]

# === КЛЮЧИ, СВЯЗАННЫЕ С ФОНОВЫМИ ЗАДАЧАМИ (WORKERS) ===

# --- Временное хранилище данных для задач ---
# Шаблон для ключа, хранящего "тяжелые" данные для задачи (тип: Hash)
KEY_TASK_BATCH_DATA = "task:batch_data:{batch_id}"

# --- Статусы задач ---
# Шаблон для ключа, хранящего статус выполнения задачи
KEY_TASK_STATUS = "task:status:{task_id}"

# Шаблон для ключа задачи генерации предметов
KEY_ITEM_GENERATION_TASK = "task:generation:item:{batch_id}"

# Шаблон для ключа задачи генерации персонажей
KEY_CHARACTER_GENERATION_TASK = "task:generation:character:{batch_id}"

# Очередь для воркера генерации предметов (если используется в ARQ)
# ITEM_GENERATION_WORKER_QUEUE_NAME уже определена выше