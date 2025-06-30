# game_server/game_services/game_world_state_orchestrator.py

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status, HTTPException

from game_server.config.logging.logging_setup import app_logger as logger

# <<< ИЗМЕНЕНО: Импортируем агрегатор и сборщик для этого сервиса
from game_server.core.dependency_aggregator import initialize_all_dependencies, shutdown_all_dependencies
from game_server.core.service_builders import build_game_world_dependencies

# --- Импортируем наши главные координаторы ---
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.coordinator_pre_start import GeneratorPreStart
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_orchestrator import CoordinatorOrchestrator
from game_server.game_services.command_center.coordinator_command.coordinator_listener import CoordinatorListener
from game_server.game_services.command_center.coordinator_command import coordinator_config

# --- Импорты фабрики сессий и движок для FastAPI Lifespan ---
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal


@asynccontextmanager
async def lifespan_event_handler(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    logger.info("🚀 ЗАПУСК ГЛАВНОГО ОРКЕСТРАТОРА ИГРОВОГО МИРА...")
    
    runtime_coordinator = None
    
    try:
        # <<< НАЧАЛО ИЗМЕНЕНИЙ
        # 1. Инициализируем ВСЕ инфраструктурные зависимости ОДИН РАЗ
        await initialize_all_dependencies()

        # 2. Вызываем СБОРЩИК, который подготовит нужный нам набор зависимостей
        game_world_deps = await build_game_world_dependencies()
        
        # 3. Сохраняем готовый набор в стейт приложения
        app.state.dependencies = game_world_deps
        # КОНЕЦ ИЗМЕНЕНИЙ >>>

        logger.info("--- ✅ ВСЕ ГЛОБАЛЬНЫЕ ЗАВИСИМОСТИ ОРКЕСТРАТОРА УСПЕШНО ЗАПУЩЕНЫ ---")

        # --- ЭТАП 1: РЕЖИМ ПРЕДСТАРТА ---
        logger.info("--- ⚙️ Вход в режим ПРЕДСТАРТА (Pre-Start Mode) ---")

        # GeneratorPreStart требует специфического набора зависимостей, извлекаем их
        generator_coordinator = GeneratorPreStart(
            repository_manager=game_world_deps["repository_manager"],
            # Примечание: GeneratorPreStart может также потребовать рефакторинга,
            # чтобы принимать весь словарь 'dependencies' для унификации.
            app_cache_managers=game_world_deps, # Передаем весь словарь, т.к. он ожидает несколько менеджеров
            arq_redis_pool=game_world_deps["arq_redis_pool"]
        )
        app.state.generator_coordinator = generator_coordinator

        pre_start_successful = await app.state.generator_coordinator.pre_start_mode()

        if not pre_start_successful:
            logger.critical("🚨 Предстартовый режим завершился с ошибкой. Оркестратор не будет запущен.")
            sys.exit(1)

        logger.info("--- ✅ Предстартовый режим успешно завершен ---")

        # --- ЭТАП 2: РЕЖИМ ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---
        logger.info("--- ⚙️ Вход в режим ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---")

        coordinator_orchestrator = CoordinatorOrchestrator(dependencies=game_world_deps)
        
        runtime_coordinator = CoordinatorListener(
            message_bus=game_world_deps["message_bus"],
            config=coordinator_config,
            orchestrator=coordinator_orchestrator
        )
        app.state.runtime_coordinator = runtime_coordinator

        runtime_coordinator.start() 
        logger.info("--- ✅ Рантайм-координатор запущен и слушает команды ---")

        yield

    finally:
        # --- SHUTDOWN ---
        logger.info("--- 🛑 Начало процесса корректного завершения работы Главного Оркестратора ---")

        if runtime_coordinator:
            await runtime_coordinator.stop()
            logger.info("✅ Рантайм-координатор остановлен.")
            
        # <<< ИЗМЕНЕНО: Вызываем общую функцию остановки без аргументов
        await shutdown_all_dependencies()
        
        logger.info("--- ✅ Все сервисы Главного Оркестратора корректно остановлены. ---")


app = FastAPI(
    title="Game World State Orchestrator",
    description="Orchestrates pre-start generation and runtime game world processes.",
    version="1.0.0",
    lifespan=lifespan_event_handler
)

@app.get("/health", summary="Проверка состояния оркестратора")
async def health_check():
    """Проверяет, что оркестратор запущен и отвечает."""
    # <<< ИЗМЕНЕНО: Проверки теперь смотрят в единый словарь зависимостей
    if (hasattr(app.state, 'dependencies') and app.state.dependencies and
        "repository_manager" in app.state.dependencies and
        "redis_batch_store" in app.state.dependencies and
        "arq_redis_pool" in app.state.dependencies and
        "message_bus" in app.state.dependencies and
        hasattr(app.state, 'runtime_coordinator') and app.state.runtime_coordinator is not None):
        
        return Response(status_code=status.HTTP_200_OK, content="Orchestrator is healthy.")
    else:
        logger.error("Health check failed: Core components not fully initialized.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Orchestrator is not fully initialized.")
