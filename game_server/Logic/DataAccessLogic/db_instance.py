# db_instance.py


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from game_server.Logic.DataAccessLogic.SQLAlchemy.SQLAlchemy_config import engine  # Импортируем движок из конфигурации

# Создаём фабрику сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session():
    """Асинхронный генератор сессии."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_db_session_no_cache():
    """Создаёт подключение без кэширования SQL-запросов."""
    async with engine.connect() as conn:
        conn = await conn.execution_options(compiled_cache={})  # Отключение кэша
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session

async def get_db_session_orm():
    """Возвращает объект сессии для работы с ORM."""
    async with AsyncSessionLocal() as session:
        return session




