# Файл: game_server/Logic/DataAccessLogic/SQLAlchemy/worker_db_utils.py
# (или generator/utils/worker_db_utils.py, в зависимости от вашей структуры)

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

# Используем существующую фабрику сессий из db_instance.py
# Это означает, что воркеры будут использовать тот же движок и пул соединений,
# что и основное приложение, если AsyncSessionLocal не переопределена где-то еще для воркеров.


from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.services.logging.logging_setup import logger #

@asynccontextmanager
async def get_worker_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию SQLAlchemy для использования в Celery воркерах
    с управлением транзакцией (commit/rollback) и автоматическим закрытием.

    Использование:
        async with get_worker_db_session() as session:
            # работа с сессией
            pass # commit произойдет автоматически, если не было исключений

    При возникновении исключения внутри блока 'with', транзакция будет отменена (rollback),
    а исключение будет перевыброшено дальше, чтобы Celery мог его обработать.
    Сессия будет закрыта в любом случае.
    """
    session: AsyncSession = AsyncSessionLocal() #
    logger.debug("Открытие сессии БД для задачи Celery воркера.")
    try:
        yield session  # Передаем сессию в блок 'with'
        # Коммит здесь не нужен, если мы хотим, чтобы вызывающий код явно коммитил.
        # Однако, если мы хотим, чтобы этот контекстный менеджер сам управлял транзакцией,
        # то коммит должен быть здесь. Давайте сделаем так, чтобы он управлял транзакцией.
        await session.commit()
        logger.debug("Транзакция сессии БД для задачи Celery воркера успешно закоммичена.")
    except Exception as e:
        logger.error(f"Ошибка в сессии БД задачи Celery воркера, выполняется откат: {e}", exc_info=True)
        if session.in_transaction(): # Проверяем, есть ли активная транзакция перед откатом
            await session.rollback()
        elif session.is_active: # Если нет транзакции, но сессия активна и могла быть "грязной"
             # В SQLAlchemy 1.4+ AsyncSession не имеет явного expire_all(), но rollback это покроет
            await session.rollback() # На всякий случай, чтобы сбросить состояние
        raise  # Перевыбрасываем исключение, чтобы Celery мог обработать ошибку задачи
    finally:
        await session.close()
        logger.debug("Сессия БД для задачи Celery воркера закрыта.")

# Если вам нужен способ получить сессию без автоматического управления транзакцией
# (например, для сложных сценариев с несколькими коммитами/откатами внутри одной задачи),
# вы можете предоставить и такую функцию, но обычно get_worker_db_session будет предпочтительнее.

async def get_raw_worker_session() -> AsyncSession:
    """
    Возвращает "сырой" объект асинхронной сессии для Celery воркера.
    Вызывающий код полностью отвечает за commit, rollback и close.
    """
    logger.debug("Получение 'сырого' объекта сессии ORM для задачи Celery воркера.")
    return AsyncSessionLocal() #