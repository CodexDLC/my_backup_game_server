from arq.worker import Worker
from arq.connections import RedisSettings
import asyncio

# Импорты для зависимостей
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.session_managers.worker_db_utils import get_worker_db_session

# Импорты для инфраструктурных менеджеров и их инициализаторов
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import (
    initialize_app_cache_managers,
    shutdown_app_cache_managers,
    get_initialized_app_cache_managers
)
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import (
    initialize_app_post_managers,
    get_repository_manager_instance,
    shutdown_app_post_managers
)
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# Импортируем все необходимые настройки Redis напрямую из settings_core
from game_server.config.settings_core import REDIS_PASSWORD, REDIS_POOL_SIZE, REDIS_URL, REDIS_CACHE_URL
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Импортируем MessageBus (для типизации)
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus

# ИМПОРТИРУЕМ CONFIG PROVIDER
from game_server.config.provider import config


# Полные пути к функциям задач (как строки)
TASKS = [
    config.constants.arq.ARQ_TASK_GENERATE_CHARACTER_BATCH,
    config.constants.arq.ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH,
    config.constants.arq.ARQ_TASK_PROCESS_EXPLORATION,
    config.constants.arq.ARQ_TASK_PROCESS_TRAINING,
    config.constants.arq.ARQ_TASK_PROCESS_CRAFTING,
]

logger.info(f"DEBUG: REDIS_URL (RAW from settings_core): {REDIS_URL}")
logger.info(f"DEBUG: REDIS_CACHE_URL (RAW from settings_core): {REDIS_CACHE_URL}")


class WorkerSettings: # ИСПРАВЛЕНО: Класс переименован обратно в WorkerSettings
    """
    Настройки для ARQ воркера.
    """
    redis_settings = RedisSettings.from_dsn(REDIS_CACHE_URL)

    functions = TASKS

    cron_jobs = []

    @staticmethod
    async def on_startup(ctx: dict):
        logger.info("🔧 ARQ Worker startup: Инициализация зависимостей...")
        
        # 1. Инициализация менеджеров PostgreSQL (RepositoryManager)
        logger.info("🔧 ARQ Worker startup: Инициализация менеджеров PostgreSQL (RepositoryManager)...")
        app_post_init_successful = await initialize_app_post_managers(async_session_factory=AsyncSessionLocal)
        if not app_post_init_successful:
            logger.critical("🚨 ARQ Worker startup: Критическая ошибка при инициализации менеджеров PostgreSQL. Завершение работы.")
            raise RuntimeError("Failed to initialize app post managers on worker startup.")
        ctx['repository_manager'] = get_repository_manager_instance()
        logger.info("✅ Менеджеры PostgreSQL успешно инициализированы и добавлены в контекст.")

        # 2. Инициализация всех менеджеров кэша и Redis-сервисов (CentralRedisClient внутри)
        logger.info("🔧 ARQ Worker startup: Инициализация менеджеров кэша и Redis-сервисов (DB 0)...")
        cache_init_successful = await initialize_app_cache_managers(async_session_factory=AsyncSessionLocal)
        if not cache_init_successful:
            logger.critical("🚨 ARQ Worker startup: Критическая ошибка при инициализации менеджеров кэша. Завершение работы.")
            raise RuntimeError("Failed to initialize app cache managers on worker startup.")
        ctx['app_managers'] = get_initialized_app_cache_managers()
        logger.info("✅ Все менеджеры кэша и Redis-сервисов (из app_cache_initializer) успешно инициализированы и добавлены в контекст.")

        # 3. Инициализация MessageBus
        logger.info("🔧 ARQ Worker startup: Инициализация MessageBus...")
        ctx["message_bus"] = RedisMessageBus(redis_pool=ctx['redis'])
        logger.info("✅ MessageBus успешно инициализирован и добавлен в контекст.")
        
        # 4. Добавляем логгер в контекст (для удобства доступа в задачах)
        ctx['logger'] = logger
        logger.info("✅ Логгер добавлен в контекст ARQ воркера.")

        # 5. Запуск периодической задачи (если она использует те же зависимости, она должна получать их из ctx)
        logger.info("🔧 ARQ Worker startup: Запуск периодической задачи...")
        ctx["periodic_task"] = asyncio.create_task(
            WorkerSettings.run_periodic_task(ctx) # ИСПРАВЛЕНО: Использование нового имени класса
        )
        logger.info("✅ Периодическая задача запущена.")
        
        logger.info("✅ ARQ Worker startup: Зависимости успешно инициализированы.")

    @staticmethod
    async def on_job_start(ctx: dict):
        logger.debug(f"⚙️ ARQ Worker: Открытие сессии БД для задачи {ctx.get('job_id')}.")
        try:
            session_obj = get_worker_db_session(ctx['repository_manager'])
            ctx["db_session_context"] = session_obj
            ctx["db_session"] = await session_obj.__aenter__()
            logger.debug(f"✅ ARQ Worker: Сессия БД для задачи {ctx.get('job_id')} добавлена в контекст.")
        except Exception as e:
            logger.error(f"❌ ARQ Worker: Ошибка при открытии сессии БД для задачи {ctx.get('job_id')}: {e}", exc_info=True)
            raise

    @staticmethod
    async def on_job_end(ctx: dict):
        logger.debug(f"⚙️ ARQ Worker: Закрытие сессии БД для задачи {ctx.get('job_id')}.")
        db_session_context = ctx.get("db_session_context")
        if db_session_context:
            try:
                await db_session_context.__aexit__(None, None, None)
                logger.debug(f"✅ ARQ Worker: Сессия БД для задачи {ctx.get('job_id')} закрыта.")
            except Exception as e:
                logger.error(f"❌ ARQ Worker: Ошибка при закрытии сессии БД для задачи {ctx.get('job_id')}: {e}", exc_info=True)
        else:
            logger.warning(f"⚠️ ARQ Worker: Не найдена сессия БД для закрытия для задачи {ctx.get('job_id')}.")

    @staticmethod
    async def run_periodic_task(ctx: dict):
        logger = ctx.get("logger")
        from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.auto_tick_module.tick_AutoSession_Watcher import collect_and_dispatch_sessions
        
        while True:
            try:
                if logger:
                    logger.info("⏱️ Запуск периодической задачи")
                
                await collect_and_dispatch_sessions(
                    repository_manager=ctx['repository_manager'],
                    message_bus=ctx["message_bus"],
                    app_cache_managers=ctx['app_managers']
                )
                
                if logger:
                    logger.info("✅ Периодическая задача успешно выполнена")
                
                await asyncio.sleep(config.settings.runtime.PERIODIC_TASK_INTERVAL_SECONDS)
                
            except asyncio.CancelledError:
                if logger:
                    logger.info("🛑 Периодическая задача отменена")
                break
            except Exception as e:
                if logger:
                    logger.error(f"❌ Ошибка в периодической задаче: {e}", exc_info=True)
                await asyncio.sleep(config.settings.runtime.PERIODIC_TASK_ERROR_INTERVAL_SECONDS)

    @staticmethod
    async def on_shutdown(ctx: dict):
        logger = ctx.get("logger")
        if logger:
            logger.info("🛑 ARQ Worker shutdown: Завершение работы зависимостей...")
        
        periodic_task = ctx.get("periodic_task")
        if periodic_task:
            periodic_task.cancel()
            try:
                await periodic_task
            except asyncio.CancelledError:
                pass
            if logger:
                logger.info("✅ Периодическая задача остановлена")
        
        await shutdown_app_cache_managers()

        await shutdown_app_post_managers()

        from game_server.Logic.InfrastructureLogic.app_post.sql_config.sqlalchemy_settings import engine
        if engine:
            await engine.dispose()
            if logger:
                logger.info("✅ Пул подключений SQLAlchemy (движок) закрыт.")

        if logger:
            logger.info("✅ ARQ Worker shutdown: Завершение работы зависимостей выполнено.")
