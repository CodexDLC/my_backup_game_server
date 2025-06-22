# game_server/game_services/game_world_state_orchestrator.py

import asyncio
import sys
from typing import Optional, Type, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status, HTTPException
from game_server.config.settings_core import REDIS_URL, REDIS_POOL_SIZE, REDIS_PASSWORD

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Импортируем менеджер пула подключений ARQ ---
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import arq_pool_manager

# --- Импортируем наши два главных координатора ---
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.coordinator_pre_start import GeneratorPreStart
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator import Coordinator

# --- Импортируем зависимости, используемые оркестратором ---
# RedisMessageBus
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus

# PostgreSQL
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.sql_config.sqlalchemy_settings import engine # Для закрытия движка

# ИМПОРТИРУЕМ ИНИЦИАЛИЗАТОРЫ И ФУНКЦИИ SHUTDOWN ИЗ app_cache_initializer
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import (
    initialize_app_cache_managers,
    shutdown_app_cache_managers,
    get_initialized_app_cache_managers
)

# ИМПОРТИРУЕМ ИНИЦИАЛИЗАТОР И MANAGER ИЗ app_post_initializer
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import (
    initialize_app_post_managers,
    get_repository_manager_instance,
    shutdown_app_post_managers
)
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager


# Определяем функцию lifespan event handler
@asynccontextmanager
async def lifespan_event_handler(app: FastAPI):
    logger.info("🚀 ЗАПУСК ГЛАВНОГО ОРКЕСТРАТОРА ИГРОВОГО МИРА (FastAPI Lifespan Startup)...")

    # 1. Инициализация ARQ Redis Pool (для задач ARQ - DB 1)
    logger.info("🔧 Инициализация ARQ Redis Pool...")
    try:
        await arq_pool_manager.startup()
        app.state.arq_redis_pool = arq_pool_manager.arq_redis_pool
        if not app.state.arq_redis_pool:
            logger.critical("🚨 Не удалось инициализировать ARQ Redis пул. Запуск отменен.")
            sys.exit(1)
        logger.info("✅ Пул подключений ARQ Redis успешно создан.")
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации ARQ Redis: {e}", exc_info=True)
        sys.exit(1)

    # 2. Инициализация менеджеров PostgreSQL (RepositoryManager)
    logger.info("🔧 Инициализация менеджеров PostgreSQL (RepositoryManager)...")
    try:
        app_post_init_successful = await initialize_app_post_managers(async_session_factory=AsyncSessionLocal)
        
        if not app_post_init_successful:
            logger.critical("🚨 Критическая ошибка при инициализации менеджеров PostgreSQL. Запуск отменен.")
            sys.exit(1)

        app.state.repository_manager = get_repository_manager_instance()
        logger.info("✅ Менеджеры PostgreSQL успешно инициализированы.")
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации менеджеров PostgreSQL: {e}", exc_info=True)
        sys.exit(1)

    # 3. Инициализация ВСЕХ менеджеров кэша и Redis-сервисов (CentralRedisClient внутри)
    logger.info("🔧 Инициализация менеджеров кэша и Redis-сервисов (DB 0)...")
    try:
        cache_init_successful = await initialize_app_cache_managers(async_session_factory=AsyncSessionLocal)
        if not cache_init_successful:
            logger.critical("🚨 Критическая ошибка при инициализации менеджеров кэша. Запуск отменен.")
            sys.exit(1)
        app.state.app_cache_managers = get_initialized_app_cache_managers()
        logger.info("✅ Все менеджеры кэша и Redis-сервисов успешно инициализированы.")
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации менеджеров кэша: {e}", exc_info=True)
        sys.exit(1)

    # 4. Инициализация MessageBus (использует app.state.arq_redis_pool)
    logger.info("🔧 Инициализация MessageBus...")
    try:
        app.state.message_bus = RedisMessageBus(redis_pool=app.state.arq_redis_pool)
        logger.info("✅ MessageBus успешно инициализирован.")
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации MessageBus: {e}", exc_info=True)
        sys.exit(1)

    # --- ЭТАП 1: РЕЖИМ ПРЕДСТАРТА ---
    logger.info("--- ⚙️ Вход в режим ПРЕДСТАРТА (Pre-Start Mode) ---")

    generator_coordinator = GeneratorPreStart(
        repository_manager=app.state.repository_manager,
        app_cache_managers=app.state.app_cache_managers,
        arq_redis_pool=app.state.arq_redis_pool
    )
    app.state.generator_coordinator = generator_coordinator

    pre_start_successful = await app.state.generator_coordinator.pre_start_mode()

    if not pre_start_successful:
        logger.critical("🚨 Предстартовый режим завершился с ошибкой. Оркестратор не будет запущен.")
        sys.exit(1)

    logger.info("--- ✅ Предстартовый режим успешно завершен ---")

    # --- ЭТАП 2: РЕЖИМ ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---
    logger.info("--- ⚙️ Вход в режим ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---")

    runtime_coordinator = Coordinator(
        message_bus=app.state.message_bus,
        app_cache_managers=app.state.app_cache_managers,
        repository_manager=app.state.repository_manager # ИСПРАВЛЕНО: Добавлен аргумент repository_manager
    )
    app.state.runtime_coordinator = runtime_coordinator

    asyncio.create_task(app.state.runtime_coordinator.start())
    logger.info("--- ✅ Рантайм-координатор запущен как фоновая задача и слушает команды ---")

    # >>> ЭТО ТОЧКА, ГДЕ ПРИЛОЖЕНИЕ ГОТОВО ОБРАБАТЫВАТЬ ЗАПРОСЫ <<<
    yield

    # >>> ЭТО ТОЧКА, ГДЕ НАЧИНАЕТСЯ SHUTDOWN <<<
    logger.info("--- 🛑 Начало процесса корректного завершения работы Главного Оркестратора (FastAPI Lifespan Shutdown) ---")

    if hasattr(app.state, 'runtime_coordinator') and app.state.runtime_coordinator:
        await app.state.runtime_coordinator.stop()
        logger.info("✅ Рантайм-координатор остановлен.")

    await shutdown_app_cache_managers()

    await shutdown_app_post_managers()

    if hasattr(app.state, 'arq_redis_pool') and arq_pool_manager and arq_pool_manager.arq_redis_pool:
        await arq_pool_manager.shutdown()
        logger.info("✅ ARQ Redis Pool закрыт.")
    elif hasattr(app.state, 'arq_redis_pool') and app.state.arq_redis_pool:
        await app.state.arq_redis_pool.close()
        logger.info("✅ ARQ Redis Pool (прямое закрытие) выполнено.")

    if engine:
        await engine.dispose()
        logger.info("✅ Пул подключений SQLAlchemy (движок) закрыт.")

    logger.info("--- ✅ Все сервисы Главного Оркестратора корректно остановлены. До свидания! ---")


# Инициализация FastAPI приложения с lifespan
app = FastAPI(
    title="Game World State Orchestrator",
    description="Orchestrates pre-start generation and runtime game world processes.",
    version="1.0.0",
    lifespan=lifespan_event_handler
)

# Добавляем минимальный роут /health для мониторинга
@app.get("/health", summary="Проверка состояния оркестратора")
async def health_check():
    """Проверяет, что оркестратор запущен и отвечает."""
    if (hasattr(app.state, 'repository_manager') and app.state.repository_manager is not None and
        hasattr(app.state, 'app_cache_managers') and app.state.app_cache_managers is not None and
        hasattr(app.state, 'arq_redis_pool') and app.state.arq_redis_pool is not None and
        hasattr(app.state, 'runtime_coordinator') and app.state.runtime_coordinator is not None):
        
        return Response(status_code=status.HTTP_200_OK, content="Orchestrator is healthy.")
    else:
        logger.error("Health check failed: Core components not fully initialized.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Orchestrator is not fully initialized.")
