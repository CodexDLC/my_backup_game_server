
# game_server\config\settings.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# API и серверные параметры
PUBLIC_GAME_SERVER_API = os.getenv("PUBLIC_GAME_SERVER_API")
INTERNAL_GAME_SERVER_API = os.getenv("INTERNAL_GAME_SERVER_API")
GAME_SERVER_API = os.getenv("GAME_SERVER_API")
RANDOM_API_URL = os.getenv("RANDOM_API_URL")

# Discord-бот
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX")

# База данных PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC") or DATABASE_URL.replace("+asyncpg", "")

# Redis и пул генерации
REDIS_URL = os.getenv("REDIS_URL", "redis://:Xv9qLr8Z9@redis:6379/0")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # 📌 Загружаем пароль из окружения
if not REDIS_PASSWORD:
    raise ValueError("❌ Ошибка: переменная окружения REDIS_PASSWORD не задана!")

REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 10))

REDIS_CHANNELS = {
    "coordinator": os.getenv("REDIS_COORDINATOR_CHANNEL", "coordinator_channel"),
    "tasks": os.getenv("REDIS_TASKS_CHANNEL", "task_channel"),
    "worker": os.getenv("REDIS_WORKER_CHANNEL", "worker_channel"),
    "alerts": os.getenv("REDIS_ALERTS_CHANNEL", "alerts_channel"),
    "system": os.getenv("REDIS_SYSTEM_CHANNEL", "system_channel")
}

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)