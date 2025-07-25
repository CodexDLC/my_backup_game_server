# game_server/game_services/system_services_main.py

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
import inject

# Импортируем функции инициализации/остановки DI-контейнера
from game_server.core.di_container import initialize_di_container, shutdown_di_container

# Импортируем ОБА класса слушателей
from game_server.game_services.command_center.system_services_command.system_services_cache_listener import CacheRequestCommandListener
from game_server.game_services.command_center.system_services_command.system_services_listener import SystemServicesCommandListener
# ✅ НОВЫЙ ИМПОРТ


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    logger.info("--- 🚀 Запуск микросервиса SystemServices ---")
    
    command_listener: SystemServicesCommandListener | None = None
    # ✅ НОВАЯ ПЕРЕМЕННАЯ для второго слушателя
    cache_listener: CacheRequestCommandListener | None = None
    current_logger = logger 
    
    try:
        # 1. Инициализируем DI-контейнер
        await initialize_di_container()

        # 2. Получаем все необходимые зависимости напрямую из inject
        command_listener = inject.instance(SystemServicesCommandListener)
        # ✅ Получаем второго слушателя
        cache_listener = inject.instance(CacheRequestCommandListener)
        current_logger = inject.instance(logging.Logger)

        # 3. Запускаем прослушивание команд
        command_listener.start()
        current_logger.info("✅ Слушатель команд (SystemServicesCommandListener) запущен.")
        
        # ✅ Запускаем второго слушателя
        cache_listener.start()
        current_logger.info("✅ Слушатель запросов к кэшу (CacheRequestCommandListener) запущен.")
        
        yield

    finally:
        # --- SHUTDOWN ---
        current_logger.info("--- 🛑 Начало процесса корректного завершения работы ---")
        
        if command_listener:
            await command_listener.stop()
            current_logger.info("🔗 SystemServicesCommandListener остановлен.")

        # ✅ Останавливаем второго слушателя
        if cache_listener:
            await cache_listener.stop()
            current_logger.info("🔗 CacheRequestCommandListener остановлен.")
        
        await shutdown_di_container()
        
        current_logger.info("--- ✅ Сервис SystemServices корректно остановлен ---")


app = FastAPI(
    title="System Services Microservice",
    description="Handles system-level commands and operations.",
    lifespan=lifespan
)