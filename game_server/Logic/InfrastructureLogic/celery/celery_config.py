# game_server\Logic\InfrastructureLogic\celery\celery_config.py

import os
from kombu import Queue
from celery.schedules import crontab # 🔥 НОВОЕ: Для гибкого расписания 🔥

from game_server.settings import RABBITMQ_URL, REDIS_URL


CELERY_broker_url = RABBITMQ_URL # Celery ожидает имя переменной без нижнего подчеркивания в конце
result_backend = REDIS_URL # Celery ожидает имя переменной без нижнего подчеркивания в конце

CELERY_timezone = "UTC"
CELERY_enable_utc = True

CELERY_result_expires = 180 # 3 минуты (180 секунд)

# --- ДОБАВЛЕНО: Настройка транспорта для бэкенда результатов ---
CELERY_result_backend_transport_options = {
    'result_key_prefix': 'task_results:' # <-- Новый префикс
}

# 🔥 НОВЫЕ ОЧЕРЕДИ 🔥
CELERY_task_queues = (
    Queue('character_generation_worker_queue', routing_key='character_generation_worker_queue'),
    Queue('item_generation_worker_queue', routing_key='item_generation_worker_queue'),
    # НОВАЯ СТРОКА: Очередь для воркеров тиков (RABBITMQ_QUEUE_TICK_WORKER)
    Queue('tick_coordinator_worker_queue', routing_key='tick_coordinator_worker_queue'),
    # НОВАЯ СТРОКА: Очередь для команд координатору (COORDINATOR_COMMAND_QUEUE)
    Queue('tick_coordinator_command_queue', routing_key='tick_coordinator_command_queue'),
)

# 🔥 НОВОЕ: Настройка расписания Celery Beat 🔥
CELERY_beat_schedule = {
    # НОВОЕ: Расписание для запуска Watcher'а
    "run_watcher_check_schedule": {
        "task": "game_server.Logic.InfrastructureLogic.celery.task.tasks_watcher.run_watcher_task", # Путь к Celery-задаче Watcher'а
        "schedule": crontab(minute='*'), # Запускать каждую минуту. Используйте `60.0` для 60 секунд.
        "options": {"queue": "watcher_queue"} # Очередь, которую будет слушать воркер, выполняющий задачи Watcher'а
    },
}

# 🔥 ВАЖНО: Добавляем пути для autodiscover_tasks
# Эти пути будут добавлены в Celery-приложение.
CELERY_imports = (
    "game_server.Logic.InfrastructureLogic.celery.task.tasks_character_generation",
    "game_server.Logic.InfrastructureLogic.celery.task.tasks_item_generation",
    "game_server.Logic.InfrastructureLogic.celery.task.tasks_tick_processing", # Наша новая задача для обработки тиков
    "game_server.Logic.InfrastructureLogic.celery.task.tasks_watcher", # Наша новая задача для Watcher'а
    
)