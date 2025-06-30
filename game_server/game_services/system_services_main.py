# game_server/game_services/system_services_main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import Dict, Any

# <<< ИЗМЕНЕНО: Импортируем агрегатор и сборщик для этого сервиса
from game_server.core.dependency_aggregator import initialize_all_dependencies, shutdown_all_dependencies
from game_server.core.service_builders import build_system_services_dependencies
from game_server.config.logging.logging_setup import app_logger as logger

# Остальные импорты остаются без изменений
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.game_services.command_center.system_services_command import system_services_config
from game_server.game_services.command_center.system_services_command.system_services_listener import SystemServicesCommandListener
from game_server.Logic.ApplicationLogic.SystemServices.system_services_orchestrator import SystemServicesOrchestrator
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    logger.info("--- 🚀 Запуск микросервиса SystemServices ---")
    
    command_listener = None
    
    try:
        # <<< НАЧАЛО ИЗМЕНЕНИЙ
        # 1. Инициализируем ВСЕ инфраструктурные зависимости ОДИН РАЗ
        await initialize_all_dependencies()

        # 2. Вызываем СБОРЩИК, который подготовит нужный нам набор зависимостей
        system_deps = await build_system_services_dependencies()

        # 3. Сохраняем готовый набор в стейт приложения
        app.state.dependencies = system_deps
        message_bus: IMessageBus = system_deps["message_bus"]
        # КОНЕЦ ИЗМЕНЕНИЙ >>>

        # 4. Создаем экземпляр ОРКЕСТРАТОРА, передав ему готовый набор зависимостей
        orchestrator = SystemServicesOrchestrator(dependencies=system_deps)
        
        # 5. Создаем экземпляр СЛУШАТЕЛЯ, передав ему оркестратор
        command_listener = SystemServicesCommandListener(
            message_bus=message_bus,
            config=system_services_config,
            orchestrator=orchestrator
        )
        
        # 6. Запускаем слушателя
        command_listener.start()
        logger.info("--- ✅ Сервис SystemServices успешно запущен и готов к работе ---")
        yield

    finally:
        # --- SHUTDOWN ---
        logger.info("--- 🛑 Начало процесса корректного завершения работы сервиса SystemServices ---")
        if command_listener:
            await command_listener.stop()
            logger.info("🔗 SystemServicesCommandListener остановлен.")
        
        # <<< ИЗМЕНЕНО: Вызываем общую функцию остановки без аргументов
        await shutdown_all_dependencies()
        
        logger.info("--- ✅ Сервис SystemServices корректно остановлен ---")


app = FastAPI(lifespan=lifespan)
