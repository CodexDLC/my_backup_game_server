# SQLAlchemy_config.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # Импортируем AsyncSession
from sqlalchemy.orm import sessionmaker

# Загрузка переменных окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Получение переменных для подключения к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан в .env")

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Для вывода SQL-запросов в лог
    future=True
)

# Создание фабрики сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,  # Указываем правильный класс AsyncSession
    expire_on_commit=False
)
