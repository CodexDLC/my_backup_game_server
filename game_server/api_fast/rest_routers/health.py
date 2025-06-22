# game_server/api_rest/routers/health.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from game_server.Logic.InfrastructureLogic.db_instance import check_db_connection, get_db_session
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

router = APIRouter(tags=["Health Check"]) # Убрал prefix, чтобы /health был корневым, как у вас сейчас.

@router.get("/health", summary="Проверка здоровья сервиса")
async def health_check(
    db_session: AsyncSession = Depends(get_db_session) # Используем сессию для проверки БД
):
    """
    Проверяет общее состояние сервиса, включая подключение к базе данных
    и другим ключевым зависимостям (например, Redis).
    """
    logger.info("Получен запрос на проверку здоровья приложения.")

    # Проверка Redis (если у вас есть redis_manager в app.state или доступен глобально)
    # Предполагаем, что app.state.rp_manager.redis доступен только в FastAPI app,
    # поэтому для роута здесь нужно будет передать его, или сделать глобальный объект.
    # Пока что оставим как есть, но это место, где вы бы интегрировали реальную проверку Redis.
    redis_status = "unknown"
    # if hasattr(app.state, 'rp_manager') and app.state.rp_manager.redis:
    #     try:
    #         await app.state.rp_manager.ping() # Пример метода для проверки соединения Redis
    #         redis_status = "connected"
    #     except Exception as e:
    #         logger.error(f"Ошибка при проверке Redis: {e}", exc_info=True)
    #         redis_status = "disconnected"
    # else:
    #     redis_status = "not_initialized" # Или другое состояние, если менеджер не инициализирован

    # Проверка БД с использованием вашей функции check_db_connection
    # Обратите внимание, что check_db_connection уже использует get_db_session внутри себя.
    # Если вы хотите использовать сессию, полученную через Depends,
    # вам нужно будет изменить check_db_connection, чтобы она принимала сессию.
    # Но так как она уже обернута в get_db_session, оставлю как есть, это более самодостаточно.
    db_ok = await check_db_connection() # Используем вашу утилитарную функцию
    
    if not db_ok:
        logger.error("Проверка здоровья: Соединение с базой данных не работает.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "База данных недоступна.",
                "db_status": "disconnected",
                "redis_status": redis_status,
                "version": os.getenv("APP_VERSION", "dev")
            }
        )

    # Если все проверки прошли, возвращаем успешный статус
    return {
        "status": "healthy",
        "services": ["discord", "system", "character", "random"], # Список ваших сервисов
        "db_status": "connected",
        "redis_status": redis_status, # Если вы реализуете эту проверку
        "version": os.getenv("APP_VERSION", "dev")
    }

health_router = router