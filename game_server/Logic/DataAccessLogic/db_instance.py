import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from game_server.server_config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from contextlib import asynccontextmanager

# ── Загрузка .env ──
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(project_root, ".env"))
# ── /Загрузка .env ──

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан в .env")

# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Для вывода SQL-запросов в лог
    future=True
)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Асинхронный контекстный менеджер для работы с сессиями SQLAlchemy
@asynccontextmanager
async def get_db_session():
    # Создаем сессию для работы с базой данных
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Передаем сессию в блок с async with
        finally:
            # Сессия будет закрыта автоматически при выходе из блока
            pass
