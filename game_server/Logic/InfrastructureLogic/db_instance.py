# game_server/Logic/InfrastructureLogic/DataAccessLogic/db_instance.py

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # <--- create_async_engine теперь здесь, если нужен для temp_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from typing import Any, AsyncGenerator, Optional

# Используем ваш новый путь для импорта engine
from game_server.Logic.InfrastructureLogic.app_post.sql_config.sqlalchemy_settings import engine # <--- ИЗМЕНЕНО

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # <--- ИЗМЕНЕНО

# 🔹 Фабрики сессий
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ---
## Основные методы получения сессий (генераторы)
# Эти методы предназначены для использования с FastAPI Depends,
# где FastAPI управляет жизненным циклом сессии (commit/rollback/close).

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная сессия для общих запросов.
    Используется как асинхронный генератор для Depends в FastAPI.
    """
    logger.debug("Открытие новой сессии БД для общего запроса.")
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        logger.debug("Сессия БД закрыта (общий запрос).")

async def get_db_session_no_cache() -> AsyncGenerator[AsyncSession, None]:
    """
    Создание подключения без кэширования SQL-запросов.
    Полезно для операций, требующих "свежих" данных, или для предотвращения нежелательного кэширования.
    """
    logger.debug("Открытие новой сессии БД без кэширования.")
    
    # ВНИМАНИЕ: temp_engine также должен использовать NullPool, если он может быть вызван в разных потоках.
    # pool_size и max_overflow не нужны с NullPool, т.к. NullPool не использует эти параметры.
    temp_engine = create_async_engine(engine.url, poolclass=NullPool) # <--- ИЗМЕНЕНО: create_async_engine здесь
    TempAsyncSessionLocal = sessionmaker(bind=temp_engine, class_=AsyncSession, expire_on_commit=False)

    async with temp_engine.connect() as conn:
        # conn = await conn.execution_options(compiled_cache={}) # Убрано, т.к. может быть несовместимо с NullPool
        async with TempAsyncSessionLocal(bind=conn) as session:
            try:
                yield session
            except SQLAlchemyError as e:
                logger.error(f"Ошибка SQLAlchemy в get_db_session_no_cache, выполняется откат: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Непредвиденная ошибка в get_db_session_no_cache, выполняется откат: {e}", exc_info=True)
                raise
            finally:
                await temp_engine.dispose()
                logger.debug("Сессия БД закрыта (без кэширования).")

async def get_db_session_orm() -> AsyncSession:
    """
    Возвращает объект асинхронной сессии для прямого использования с ORM.
    Требует ручного управления коммитом, откатом и закрытием.
    """
    logger.debug("Получение прямого объекта сессии ORM.")
    session = AsyncSessionLocal()
    return session

async def check_db_connection() -> bool:
    """
    Проверяет соединение с базой данных.
    Возвращает True, если соединение успешно, иначе False.
    """
    logger.info("Проверка соединения с базой данных...")
    try:
        async with engine.connect() as conn:
            logger.info("Соединение с базой данных успешно установлено.")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Ошибка соединения с базой данных: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при проверке соединения с БД: {e}", exc_info=True)
        return False

async def get_raw_connection() -> Optional[Any]:
    """
    Возвращает сырое асинхронное соединение с базой данных.
    Полезно для выполнения низкоуровневых запросов, которые не требуют ORM.
    Требует ручного закрытия соединения.
    """
    logger.debug("Получение сырого соединения с базой данных.")
    try:
        conn = await engine.connect()
        return conn
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении сырого соединения с БД: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении сырого соединения: {e}", exc_info=True)
        return None