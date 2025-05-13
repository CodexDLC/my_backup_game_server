# redis_config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем параметры подключения к Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Путь к Redis
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 10))  # Размер пула подключений

# Пример для Celery
CELERY_BROKER_URL = REDIS_URL  # Указание на Redis как брокер для Celery
CELERY_RESULT_BACKEND = REDIS_URL  # Использование Redis для хранения результатов

print(f"Redis URL: {REDIS_URL}")
