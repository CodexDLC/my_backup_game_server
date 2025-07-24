import sys
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Response, status, HTTPException

# 🔥 ИЗМЕНЕНИЕ: Импортируем функции инициализации/остановки DI-контейнера
from game_server.core.di_container import initialize_di_container, shutdown_di_container


# Импорты для главных координаторов (теперь они будут браться из inject)
from game_server.Logic.ApplicationLogic.world_orchestrator.pre_start.coordinator_pre_start import PreStartCoordinator
from game_server.Logic.ApplicationLogic.world_orchestrator.runtime.runtime_coordinator import RuntimeCoordinator
from game_server.game_services.command_center.coordinator_command.coordinator_listener import CoordinatorListener


# Импорты для инфраструктуры

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus # Если нужен для типизации




import inject # 🔥 Импортируем inject


@asynccontextmanager
async def lifespan_event_handler(app: FastAPI):
    """
    Управляет жизненным циклом сервиса: инициализация и корректное завершение.
    """
    current_logger: logging.Logger = logging.getLogger(__name__) # Или inject.instance(logging.Logger) если DI уже настроен для этого уровня

    current_logger.info("🚀 ЗАПУСК ГЛАВНОГО ОРКЕСТРАТОРА ИГРОВОГО МИРА...")

    runtime_coordinator_listener = None
    
    try:
        # 🔥 ИЗМЕНЕНИЕ: Инициализируем DI-контейнер, который сам инициализирует все зависимости
        # Это также обеспечит правильное связывание логгера.
        await initialize_di_container()

        # 🔥 ИЗМЕНЕНИЕ: Получаем оркестраторы и другие необходимые глобальные зависимости напрямую из inject
        pre_start_coordinator: PreStartCoordinator = inject.instance(PreStartCoordinator)
        runtime_coordinator_instance: RuntimeCoordinator = inject.instance(RuntimeCoordinator) # Класс RuntimeCoordinator
        message_bus: IMessageBus = inject.instance(IMessageBus) # Получаем из inject


        current_logger.info("--- ✅ ВСЕ ГЛОБАЛЬНЫЕ ЗАВИСИМОСТИ ОРКЕСТРАТОРА УСПЕШНО ЗАПУЩЕНЫ ---")

        # --- ЭТАП 1: РЕЖИМ ПРЕДСТАРТА ---
        current_logger.info("--- ⚙️ Вход в режим ПРЕДСТАРТА (Pre-Start Mode) ---")

        # 🔥 ИЗМЕНЕНИЕ: Используем полученный из inject pre_start_coordinator
        app.state.generator_coordinator = pre_start_coordinator # Сохраняем для доступа в app.state

        pre_start_successful = await app.state.generator_coordinator.run_pre_start_sequence()

        if not pre_start_successful:
            current_logger.critical("🚨 Предстартовый режим завершился с ошибкой. Оркестратор не будет запущен.")
            sys.exit(1)

        current_logger.info("--- ✅ Предстартовый режим успешно завершен ---")

        # --- ЭТАП 2: РЕЖИМ ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---
        current_logger.info("--- ⚙️ Вход в режим ОСНОВНОЙ РАБОТЫ (Runtime Mode) ---")

        # 🔥 ИЗМЕНЕНИЕ: Используем полученный из inject runtime_coordinator_instance
        coordinator_orchestrator = runtime_coordinator_instance
        
        # 🔥 ИЗМЕНЕНИЕ: УДАЛИТЬ 'config=coordinator_config'
        runtime_coordinator_listener = CoordinatorListener(
            message_bus=message_bus, # Используем message_bus из inject
            # config=coordinator_config, # <-- УДАЛИТЬ ЭТУ СТРОКУ
            orchestrator=coordinator_orchestrator
        )
        app.state.runtime_coordinator = runtime_coordinator_listener # Сохраняем для доступа в app.state

        runtime_coordinator_listener.start() 
        current_logger.info("--- ✅ Рантайм-координатор запущен и слушает команды ---")

        yield

    finally:
        # --- SHUTDOWN ---
        current_logger.info("--- 🛑 Начало процесса корректного завершения работы Главного Оркестратора ---")

        if runtime_coordinator_listener:
            await runtime_coordinator_listener.stop()
            current_logger.info("✅ Рантайм-координатор остановлен.")
            
        # 🔥 ИЗМЕНЕНИЕ: Вызываем общую функцию остановки DI-контейнера
        await shutdown_di_container()
        
        current_logger.info("--- ✅ Все сервисы Главного Оркестратора корректно остановлены. ---")


app = FastAPI(
    title="Game World State Orchestrator",
    description="Orchestrates pre-start generation and runtime game world processes.",
    version="1.0.0",
    lifespan=lifespan_event_handler
)

@app.get("/health", summary="Проверка состояния оркестратора")
async def health_check():
    """Проверяет, что оркестратор запущен и отвечает."""
    # 🔥 ИЗМЕНЕНИЕ: Проверки теперь смотрят в единый DI-контейнер через inject.instance()
    # Это более надежный способ, чем проверять app.state.dependencies напрямую,
    # так как inject гарантирует наличие зависимостей, если они сконфигурированы.
    try:
        # Попытка получить ключевые зависимости, чтобы убедиться, что inject работает
        inject.instance(IMessageBus)
        inject.instance(PreStartCoordinator)
        inject.instance(RuntimeCoordinator)
        inject.instance(logging.Logger) # Проверим, что логгер доступен

        # Если дошли сюда, значит, основные зависимости доступны через inject
        return Response(status_code=status.HTTP_200_OK, content="Orchestrator is healthy.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Orchestrator is not fully initialized or DI container is not ready.")