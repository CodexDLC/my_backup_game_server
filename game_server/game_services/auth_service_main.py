# game_server/game_services/auth_service_main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
import logging
import inject # 🔥 Импортируем inject

# Импортируем функции инициализации/остановки DI-контейнера
from game_server.core.di_container import initialize_di_container, shutdown_di_container

# Импорты классов, которые теперь будут извлекаться из inject
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator
from game_server.game_services.command_center.auth_service_command.auth_issue_token_rpc import AuthIssueTokenRpc
from game_server.game_services.command_center.auth_service_command.auth_service_listener import AuthServiceCommandListener
from game_server.game_services.command_center.auth_service_command.auth_service_rpc_handler import AuthServiceRpcHandler
# 🔥 ИЗМЕНЕНО: Импортируем переименованный класс AuthIssueTokenRpc


# 🔥 ДОБАВЛЕНО: Импортируем роутер для проверок здоровья
from game_server.game_services.healthcheck.auth_service_healthcheck_route import health_check_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    # Получение экземпляра логгера для текущего модуля.
    current_logger: logging.Logger = logging.getLogger(__name__)

    # Вывод сообщения о начале запуска микросервиса.
    print("--- 🚀 Запуск микросервиса Аутентификации ---")
        
    # Инициализация переменных для слушателей (по умолчанию None).
    command_listener = None
    rpc_handler = None 
    issue_token_rpc_handler = None 
    
    # Начало блока try-finally для управления жизненным циклом.
    try:
        # Асинхронный вызов функции для инициализации DI-контейнера.
        await initialize_di_container()

        # Получение экземпляра оркестратора аутентификации из DI-контейнера.
        orchestrator = inject.instance(AuthOrchestrator) 
        # Получение экземпляра шины сообщений из DI-контейнера.
        message_bus = inject.instance(IMessageBus)
        # Получение экземпляра менеджера сессий из DI-контейнера.
        session_manager = inject.instance(ISessionManager)
        # Получение экземпляра логгера из DI-контейнера (для использования в текущем контексте).
        current_logger = inject.instance(logging.Logger)

        # --- Получение и логирование слушателей ---
        # Получение экземпляра слушателя команд аутентификации из DI-контейнера.
        command_listener = inject.instance(AuthServiceCommandListener) 
        current_logger.info(f"Type of command_listener: {type(command_listener)}") 
        
        # Получение экземпляра RPC-обработчика аутентификации из DI-контейнера.        
        rpc_handler = inject.instance(AuthServiceRpcHandler)
        current_logger.info(f"Type of rpc_handler: {type(rpc_handler)}") 
        
        # Получение экземпляра RPC-обработчика выдачи токенов из DI-контейнера.
        issue_token_rpc_handler = inject.instance(AuthIssueTokenRpc) # 🔥 ИЗМЕНЕНО: Инициализируем переименованный класс
        current_logger.info(f"Type of issue_token_rpc_handler: {type(issue_token_rpc_handler)}") 

        # Сохранение экземпляра оркестратора в состоянии приложения FastAPI.
        app.state.orchestrator = orchestrator
        # Сохранение экземпляра шины сообщений в состоянии приложения FastAPI.
        app.state.message_bus = message_bus
        # Сохранение экземпляра менеджера сессий в состоянии приложения FastAPI.
        app.state.session_manager = session_manager
        # Сохранение экземпляра логгера в состоянии приложения FastAPI.
        app.state.logger = current_logger
        # Сохранение экземпляра слушателя команд в состоянии приложения FastAPI.
        app.state.command_listener = command_listener
        # Сохранение экземпляра RPC-обработчика в состоянии приложения FastAPI.
        app.state.rpc_handler = rpc_handler
        # Сохранение экземпляра RPC-обработчика выдачи токенов в состоянии приложения FastAPI.
        app.state.issue_token_rpc_handler = issue_token_rpc_handler
        
        # --- Запуск слушателей ---
        # Запуск RPC-слушателя для валидации токенов.
        # Метод start() в BaseMicroserviceListener создает и управляет внутренней задачей _listen_loop
        rpc_handler.start()
        # Запуск RPC-слушателя для выдачи токенов.
        issue_token_rpc_handler.start()

        # Запуск основного слушателя команд.
        command_listener.start() 
        
        # Логирование успешного запуска сервиса.
        current_logger.info("--- ✅ Сервис Аутентификации успешно запущен и готов к работе ---")
        # Передача управления FastAPI для обработки запросов.
        yield

    # Блок finally, который гарантированно выполнится при завершении или ошибке.
    finally:
        # Логирование начала процесса завершения работы сервиса.
        current_logger.info("--- 🛑 Начало процесса корректного завершения работы сервиса Аутентификации ---")
        
        # Проверка наличия слушателя команд и его остановка.
        if command_listener:
            await command_listener.stop()
        
        # Проверка наличия RPC-обработчика и его остановка.
        if rpc_handler: 
            await rpc_handler.stop()
        
        # Проверка наличия RPC-обработчика выдачи токенов и его остановка.
        if issue_token_rpc_handler: 
            await issue_token_rpc_handler.stop()

        # Вызов общей функции для корректного завершения работы DI-контейнера.
        await shutdown_di_container()
        
        # Логирование успешного завершения работы сервиса.
        current_logger.info("--- ✅ Сервис Аутентификации корректно остановлен ---")


app = FastAPI(lifespan=lifespan)

# Подключаем роутер для проверок здоровья
app.include_router(health_check_router, prefix="/health")

# Добавьте пример роута для проверки работоспособности, если необходимо
@app.get("/")
async def read_root():
    return {"message": "AuthService is running"}