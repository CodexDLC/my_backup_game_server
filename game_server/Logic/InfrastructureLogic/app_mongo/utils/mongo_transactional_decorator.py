# game_server/Logic/InfrastructureLogic/app_mongo/utils/mongo_transactional_decorator.py

import functools
import logging
from typing import Callable, Any, Coroutine, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

# Используем тот же логгер, что и в проекте
logger = logging.getLogger(__name__)

def mongo_transactional():
    """
    Декоратор для асинхронных методов, работающих с MongoDB.
    Обеспечивает общую обертку для обработки ошибок и логирования
    операций, связанных с MongoDB.

    ВАЖНО: Этот декоратор не управляет явными транзакциями MongoDB
    для многодокументных операций. Он предназначен для методов,
    где операции с базой данных атомарны на уровне одной операции/документа,
    или где транзакционность управляется внутри репозитория/сервиса MongoDB
    (например, через AsyncIOMotorClient.start_session()).
    Он фокусируется на централизованной обработке исключений MongoDB.
    """
    def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                # В этом декораторе мы не инжектируем сессию в аргументы метода,
                # так как репозитории MongoDB должны управлять своими соединениями/сессиями.
                # Он просто оборачивает вызов метода для обработки ошибок.
                result = await func(*args, **kwargs)
                logger.debug(f"Метод {func.__name__} успешно выполнен (MongoDB-операция).")
                return result
            except Exception as e:
                logger.error(
                    f"Ошибка в MongoDB-операции метода {func.__name__}: {e}",
                    exc_info=True # Включаем полный traceback в лог
                )
                # Перебрасываем исключение, чтобы вызывающий код мог его обработать
                raise
        return wrapper
    return decorator