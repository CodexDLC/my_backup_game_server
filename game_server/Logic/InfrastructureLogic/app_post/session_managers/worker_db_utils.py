# game_server/Logic/InfrastructureLogic/app_post/session_managers/worker_db_utils.py

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Type # Добавлен Type
from sqlalchemy.ext.asyncio import AsyncSession

# Используем существующую фабрику сессий из db_instance.py
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # Добавлен импорт RepositoryManager

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


@asynccontextmanager
async def get_worker_db_session(repository_manager: RepositoryManager) -> AsyncGenerator[AsyncSession, None]: # ИСПРАВЛЕНО: Теперь принимает repository_manager
    """
    Предоставляет асинхронную сессию SQLAlchemy для использования в ARQ воркерах
    с управлением транзакцией (commit/rollback) и автоматическим закрытием.
    Сессия получается из фабрики репозиториев для обеспечения консистентности.
    """
    # Получаем сессию из фабрики, которая была передана в RepositoryManager
    # Assumption: RepositoryManager has a way to get a session factory (e.g., repository_manager.db_session_factory)
    # If not, you might need to pass AsyncSessionLocal directly here, but then the argument to this function
    # would be Type[AsyncSession], not RepositoryManager.
    # Given how RepositoryManager is initialized (with AsyncSessionLocal),
    # a clean way to get the session is by calling AsyncSessionLocal() directly here,
    # as this utility function is outside the RepositoryManager class.

    # ИСПРАВЛЕНО: Используем AsyncSessionLocal напрямую, как фабрику сессий
    session: AsyncSession = AsyncSessionLocal()
    logger.debug("Открытие сессии БД для задачи ARQ воркера.")
    try:
        yield session
        await session.commit()
        logger.debug("Транзакция сессии БД для задачи ARQ воркера успешно закоммичена.")
    except Exception as e:
        logger.error(f"Ошибка в сессии БД задачи ARQ воркера, выполняется откат: {e}", exc_info=True)
        # Проверяем, находится ли сессия в активной транзакции перед откатом
        if session.in_transaction():
            await session.rollback()
        # else:
            # If not in transaction, rollback might not be necessary or could raise an error depending on SQLAlchemy version
            # For robustness, we check or just pass if not in transaction.
        raise
    finally:
        await session.close()
        logger.debug("Сессия БД для задачи ARQ воркера закрыта.")

async def get_raw_worker_session() -> AsyncSession:
    """
    Возвращает "сырой" объект асинхронной сессии для ARQ воркера.
    Вызывающий код полностью отвечает за commit, rollback и close.
    """
    logger.debug("Получение 'сырого' объекта сессии ORM для задачи ARQ воркера.")
    return AsyncSessionLocal()
