# server_config.py
import os
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Настройки базы данных
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# Путь к схемам базы данных
DATABASE_SCHEMAS_PATH = os.path.join(os.path.dirname(__file__), 'database', 'schemas')

# (Можно добавить ещё настройки сервера здесь позже)
