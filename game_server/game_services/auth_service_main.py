# game_server/game_services/auth_service_main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

# <<< ИЗМЕНЕНО: Импортируем агрегатор и сборщик
from game_server.core.dependency_aggregator import initialize_all_dependencies, shutdown_all_dependencies
from game_server.core.service_builders import build_auth_service_dependencies
from game_server.config.logging.logging_setup import app_logger as logger

# Остальные импорты остаются без изменений
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.game_services.command_center.auth_service_command import auth_service_config
from game_server.game_services.command_center.auth_service_command.auth_service_listener import AuthServiceCommandListener
from game_server.game_services.command_center.auth_service_command.auth_service_rpc_handler import AuthServiceRpcHandler
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.game_services.command_center.auth_service_command.auth_issue_token_rpc_handler import AuthIssueTokenRpcHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    logger.info("--- 🚀 Запуск микросервиса Аутентификации ---")
    
    command_listener = None
    rpc_handler_task = None
    issue_token_rpc_handler_task = None
    
    try:
        # <<< НАЧАЛО ИЗМЕНЕНИЙ
        # 1. Инициализируем ВСЕ инфраструктурные зависимости ОДИН РАЗ
        await initialize_all_dependencies()
        
        # 2. Вызываем СБОРЩИК, который подготовит нужный нам набор зависимостей
        auth_deps = await build_auth_service_dependencies()
        
        # 3. Сохраняем готовый набор в стейт приложения
        app.state.dependencies = auth_deps
        message_bus: IMessageBus = auth_deps["message_bus"]
        # КОНЕЦ ИЗМЕНЕНИЙ >>>

        # 4. Создаем экземпляр ОРКЕСТРАТОРА, передавая ему готовый набор зависимостей
        orchestrator = AuthOrchestrator(dependencies=auth_deps)
        
        # 5. Создаем экземпляр СЛУШАТЕЛЯ КОМАНД
        command_listener = AuthServiceCommandListener(
            message_bus=message_bus,
            config=auth_service_config,
            orchestrator=orchestrator
        )
        
        # 6. Создаем и запускаем обработчик RPC-запросов (для валидации токенов)
        rpc_handler = AuthServiceRpcHandler(
            message_bus=message_bus,
            orchestrator=orchestrator
        )
        rpc_handler_task = asyncio.create_task(rpc_handler.start_listening())

        # 7. Создаем и запускаем обработчик RPC для выдачи токенов
        issue_token_rpc_handler = AuthIssueTokenRpcHandler(
            message_bus=message_bus,
            orchestrator=orchestrator
        )
        issue_token_rpc_handler_task = asyncio.create_task(issue_token_rpc_handler.start_listening())

        # 8. Запускаем основного слушателя команд
        command_listener.start()
        
        logger.info("--- ✅ Сервис Аутентификации успешно запущен и готов к работе ---")
        yield

    finally:
        # --- SHUTDOWN ---
        logger.info("--- 🛑 Начало процесса корректного завершения работы сервиса Аутентификации ---")
        if command_listener:
            await command_listener.stop()
        
        if rpc_handler_task and not rpc_handler_task.done():
            rpc_handler_task.cancel()
            try:
                await rpc_handler_task
            except asyncio.CancelledError:
                logger.info("RPC-слушатель валидации токенов остановлен.")

        if issue_token_rpc_handler_task and not issue_token_rpc_handler_task.done():
            issue_token_rpc_handler_task.cancel()
            try:
                await issue_token_rpc_handler_task
            except asyncio.CancelledError:
                logger.info("RPC-слушатель выдачи токенов остановлен.")

        # <<< ИЗМЕНЕНО: Вызываем общую функцию остановки без аргументов
        await shutdown_all_dependencies()
        
        logger.info("--- ✅ Сервис Аутентификации корректно остановлен ---")


app = FastAPI(lifespan=lifespan)
