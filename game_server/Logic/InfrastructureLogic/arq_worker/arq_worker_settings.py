# game_server/Logic/InfrastructureLogic/arq_worker/arq_worker_settings.py

import asyncio
from arq.connections import RedisSettings

# <<< ИЗМЕНЕНО: Импортируем новую систему зависимостей
from game_server.core.dependency_aggregator import initialize_all_dependencies, shutdown_all_dependencies
from game_server.core.service_builders import build_arq_worker_dependencies

# Импорты для инфраструктуры и задач
from game_server.config.settings_core import REDIS_CACHE_URL
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.config.provider import config
from game_server.Logic.InfrastructureLogic.app_post.session_managers.worker_db_utils import get_worker_db_session

# Список задач, которые может выполнять воркер
TASKS = [
    config.constants.arq.ARQ_TASK_GENERATE_CHARACTER_BATCH,
    config.constants.arq.ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH,
    config.constants.arq.ARQ_TASK_PROCESS_EXPLORATION,
    config.constants.arq.ARQ_TASK_PROCESS_TRAINING,
    config.constants.arq.ARQ_TASK_PROCESS_CRAFTING,
]

class WorkerSettings:
    """
    Настройки для ARQ воркера, использующие новую архитектуру зависимостей.
    """
    redis_settings = RedisSettings.from_dsn(REDIS_CACHE_URL)
    functions = TASKS
    cron_jobs = []
    
    # Контекст, который будет доступен во всех задачах
    ctx = {}

    @staticmethod
    async def on_startup(ctx: dict):
        """
        Выполняется один раз при старте воркера.
        Инициализирует все зависимости и помещает их в контекст.
        """
        logger.info("🔧 ARQ Worker startup: Инициализация зависимостей...")
        try:
            # 1. Инициализируем всю инфраструктуру
            await initialize_all_dependencies()
            
            # 2. Собираем нужный набор зависимостей для воркера
            worker_deps = await build_arq_worker_dependencies()
            
            # 3. Обновляем контекст воркера, чтобы зависимости были доступны в задачах
            ctx.update(worker_deps)
            WorkerSettings.ctx.update(ctx) # Обновляем и контекст класса
            
            logger.info("✅ ARQ Worker startup: Все зависимости успешно инициализированы.")

            # Запускаем периодическую задачу, если она нужна
            logger.info("🔧 ARQ Worker startup: Запуск периодической задачи...")
            ctx["periodic_task"] = asyncio.create_task(
                WorkerSettings.run_periodic_task(ctx)
            )
            logger.info("✅ Периодическая задача запущена.")

        except Exception as e:
            logger.critical(f"🚨 ARQ Worker startup: Критическая ошибка: {e}", exc_info=True)
            await WorkerSettings.on_shutdown(ctx)
            raise

    @staticmethod
    async def on_job_start(ctx: dict):
        """Выполняется перед каждой задачей для управления сессией БД."""
        logger.debug(f"⚙️ ARQ Worker: Открытие сессии БД для задачи {ctx.get('job_id')}.")
        try:
            repository_manager = ctx['repository_manager']
            session_obj = get_worker_db_session(repository_manager)
            ctx["db_session_context"] = session_obj
            ctx["db_session"] = await session_obj.__aenter__()
        except Exception as e:
            logger.error(f"❌ ARQ Worker: Ошибка при открытии сессии БД: {e}", exc_info=True)
            raise

    @staticmethod
    async def on_job_end(ctx: dict):
        """Выполняется после каждой задачи для закрытия сессии БД."""
        db_session_context = ctx.get("db_session_context")
        if db_session_context:
            try:
                await db_session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"❌ ARQ Worker: Ошибка при закрытии сессии БД: {e}", exc_info=True)

    @staticmethod
    async def run_periodic_task(ctx: dict):
        """Периодическая задача для выполнения фоновых операций."""
        from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.auto_tick_module.tick_AutoSession_Watcher import collect_and_dispatch_sessions
        
        while True:
            try:
                logger.info("⏱️ Запуск периодической задачи...")
                await collect_and_dispatch_sessions(
                    repository_manager=ctx['repository_manager'],
                    message_bus=ctx["message_bus"],
                    app_cache_managers=ctx # Передаем весь контекст, т.к. функция может ожидать разные менеджеры
                )
                logger.info("✅ Периодическая задача успешно выполнена.")
                await asyncio.sleep(config.settings.runtime.PERIODIC_TASK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                logger.info("🛑 Периодическая задача отменена.")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в периодической задаче: {e}", exc_info=True)
                await asyncio.sleep(config.settings.runtime.PERIODIC_TASK_ERROR_INTERVAL_SECONDS)

    @staticmethod
    async def on_shutdown(ctx: dict):
        """Выполняется один раз при остановке воркера."""
        logger.info("🛑 ARQ Worker shutdown: Завершение работы...")
        
        periodic_task = ctx.get("periodic_task")
        if periodic_task:
            periodic_task.cancel()
            try:
                await periodic_task
            except asyncio.CancelledError:
                pass
            logger.info("✅ Периодическая задача остановлена.")
        
        await shutdown_all_dependencies()
        logger.info("✅ ARQ Worker shutdown: Все зависимости корректно завершили работу.")
