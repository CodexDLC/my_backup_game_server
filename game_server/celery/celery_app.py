
# game_server\celery\celery_app.py


from celery import Celery
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Создание Celery-приложения
app = Celery("game_server")


# Загружаем конфиг из `game_server/config/celery_config.py`
app.config_from_object("game_server.celery.celery_config", namespace="CELERY")

# Автоматически ищем задачи в `game_server/celery`
app.autodiscover_tasks(["game_server.celery.task"]) 
