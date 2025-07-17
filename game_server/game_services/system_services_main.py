# game_server/game_services/system_services_main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

# Импортируем функции инициализации/остановки DI-контейнера
from game_server.core.di_container import initialize_di_container, shutdown_di_container

# Импорты для классов, которые мы будем получать из DI
from game_server.game_services.command_center.system_services_command.system_services_listener import SystemServicesCommandListener

import inject

# Получаем корневой логгер на случай, если DI еще не инициализирован
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    logger.info("--- 🚀 Запуск микросервиса SystemServices ---")
    
    command_listener: SystemServicesCommandListener | None = None
    current_logger = logger 
    
    try:
        # 1. Инициализируем DI-контейнер
        await initialize_di_container()

        # 2. Получаем все необходимые зависимости напрямую из inject
        command_listener = inject.instance(SystemServicesCommandListener)
        current_logger = inject.instance(logging.Logger)

        # 3. Запускаем прослушивание команд
        # ИСПРАВЛЕНО: Вызываем правильный метод start() и убираем await
        command_listener.start()
        current_logger.info("✅ Слушатель команд SystemServices запущен.")
        
        yield

    finally:
        # --- SHUTDOWN ---
        current_logger.info("--- 🛑 Начало процесса корректного завершения работы сервиса SystemServices ---")
        
        if command_listener:
            await command_listener.stop()
            current_logger.info("🔗 SystemServicesCommandListener остановлен.")
        
        await shutdown_di_container()
        
        current_logger.info("--- ✅ Сервис SystemServices корректно остановлен ---")


app = FastAPI(
    title="System Services Microservice",
    description="Handles system-level commands and operations.",
    lifespan=lifespan
)
