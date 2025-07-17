# game_server/game_services/healthcheck/auth_service_healthcheck_route.py

from fastapi import APIRouter, Depends, Request, HTTPException, status
import asyncio
import logging # Для логирования в роуте
import inject # Для inject.instance, если нужно

# Импорты зависимостей (для проверки их состояния)
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository # Пример репозитория для проверки БД


health_check_router = APIRouter(tags=["Health Checks"])
logger = logging.getLogger(__name__) # Отдельный логгер для роутера здоровья

@health_check_router.get("/liveness")
async def liveness_check(request: Request):
    """
    Проверка "живости" приложения.
    Возвращает 200 OK, если приложение запущено и способно отвечать на запросы.
    Не проверяет глубокое состояние зависимостей, только базовую работоспособность.
    Используется для перезапуска контейнера, если он завис.
    """
    logger.info("Liveness check received.")
    return {"status": "ok", "message": "AuthService is alive!"}

@health_check_router.get("/readiness")
async def readiness_check(request: Request):
    """
    Проверка "готовности" приложения к приему трафика.
    Проверяет состояние критически важных внутренних слушателей и соединений.
    Если какая-либо проверка не проходит, возвращает 503 Service Unavailable.
    Используется для определения, когда сервис готов принимать запросы или когда его нужно исключить из балансировки.
    """
    logger.info("Readiness check received. Performing deep health checks...")
    
    # Получаем зависимости из app.state, куда они были сохранены в lifespan
    message_bus: IMessageBus = request.app.state.message_bus
    session_manager: ISessionManager = request.app.state.session_manager
    command_listener = request.app.state.command_listener
    rpc_handler = request.app.state.rpc_handler
    issue_token_rpc_handler = request.app.state.issue_token_rpc_handler

    checks = []

    # 1. Проверка основного слушателя команд RabbitMQ
    if not command_listener or (command_listener._listen_task and command_listener._listen_task.done()):
        checks.append({"component": "AuthServiceCommandListener", "status": "down", "message": "Listener task not active"})
    else:
        checks.append({"component": "AuthServiceCommandListener", "status": "up"})

    # 2. Проверка RPC-слушателей (примерно)
    if not rpc_handler or (rpc_handler._consumer_task and rpc_handler._consumer_task.done()): # Предполагается _consumer_task
        checks.append({"component": "AuthServiceRpcHandler", "status": "down", "message": "RPC Listener task not active"})
    else:
        checks.append({"component": "AuthServiceRpcHandler", "status": "up"})

    if not issue_token_rpc_handler or (issue_token_rpc_handler._consumer_task and issue_token_rpc_handler._consumer_task.done()): # Предполагается _consumer_task
        checks.append({"component": "AuthIssueTokenRpcHandler", "status": "down", "message": "Issue Token RPC Listener task not active"})
    else:
        checks.append({"component": "AuthIssueTokenRpcHandler", "status": "up"})


    # 3. Проверка соединения с RabbitMQ
    try:
        if not hasattr(message_bus, 'connection') or not message_bus.connection or message_bus.connection.is_closed:
            raise ConnectionError("RabbitMQ connection is closed")
        # Можно добавить пинг, если message_bus предоставляет его
        # await message_bus.ping() 
        checks.append({"component": "RabbitMQ_Connection", "status": "up"})
    except Exception as e:
        checks.append({"component": "RabbitMQ_Connection", "status": "down", "message": str(e)})

    # 4. Проверка соединения с PostgreSQL (через репозиторий)
    try:
        # Для проверки БД можно попробовать выполнить легкий запрос или вызвать метод проверки
        # Вам нужно будет инжектировать или получить нужный репозиторий
        account_info_repo: IAccountInfoRepository = inject.instance(IAccountInfoRepository) # Получаем из inject
        # Предполагаем, что у вашего репозитория есть метод test_connection() или аналогичный
        # Или выполним простой запрос
        await account_info_repo.test_connection() # Вам нужно будет добавить этот метод в ваш репозиторий
        checks.append({"component": "PostgreSQL_Connection", "status": "up"})
    except Exception as e:
        checks.append({"component": "PostgreSQL_Connection", "status": "down", "message": str(e)})

    # 5. Проверка соединения с Redis (через SessionManager)
    try:
        # Аналогично, предполагаем метод test_connection() или пинг
        await session_manager.test_connection() # Вам нужно будет добавить этот метод в SessionManager
        checks.append({"component": "Redis_Connection", "status": "up"})
    except Exception as e:
        checks.append({"component": "Redis_Connection", "status": "down", "message": str(e)})

    # Проверяем, есть ли какие-либо "down" статусы
    overall_status = "ok"
    for check in checks:
        if check["status"] == "down":
            overall_status = "unready"
            break
            
    if overall_status == "unready":
        logger.warning(f"Readiness check failed. Details: {checks}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "unready", "checks": checks})
    
    logger.info("Readiness check passed.")
    return {"status": "ready", "checks": checks}