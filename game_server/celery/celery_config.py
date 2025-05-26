
# game_server\config\celery_config.py


import os


broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")


timezone = "UTC"  # 🔥 Новый формат
enable_utc = True

result_expires = 180 # 3 минуты (180 секунд)

beat_schedule = {
    "tick_task_schedule": {
        "task": "game_server.celery.task.tasks_tick.schedule_tick_task",
        "schedule": 30.0,
        "options": {"queue": "tick_queue"}  # ✅ Должно быть назначено на `tick_queue`
    },
}
