# game_server/config/constants/redis/task_keys.py

# === КЛЮЧИ, СВЯЗАННЫЕ С ФОНОВЫМИ ЗАДАЧАМИ (WORKERS) ===

# --- Временное хранилище данных для задач ---
# Шаблон для ключа, хранящего "тяжелые" данные для задачи (тип: Hash)
KEY_TASK_BATCH_DATA = "task:batch_data:{batch_id}"

# --- Статусы задач ---
# Шаблон для ключа, хранящего статус выполнения задачи
KEY_TASK_STATUS = "task:status:{task_id}"


# --- Задачи генерации контента ---

# Шаблон для ключа задачи генерации предметов
KEY_ITEM_GENERATION_TASK = "task:generation:item:{batch_id}"

# Шаблон для ключа задачи генерации персонажей
KEY_CHARACTER_GENERATION_TASK = "task:generation:character:{batch_id}"

# Очередь для воркера генерации предметов (если используется в ARQ)
ITEM_GENERATION_WORKER_QUEUE_NAME: str = "item_generation_worker_queue"