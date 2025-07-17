# game_server/Logic/InfrastructureLogic/arq_worker/arq_worker_settings.py

import asyncio
import logging
from arq.connections import RedisSettings
from typing import Dict, Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession 

from game_server.core.di_container import initialize_di_container, shutdown_di_container

from game_server.config.constants.arq import TASKS
from game_server.config.settings_core import REDIS_CACHE_URL
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.config.provider import config

# ИМПОРТЫ ЗАВИСИМОСТЕЙ ДЛЯ DI
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository, IWorldStateRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository, ICharacterPoolRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.item_generator.item_batch_processor import ItemBatchProcessor
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.character_batch_processor import CharacterBatchProcessor
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.world_map_generator.world_map_generator import WorldMapGenerator


import inject


class WorkerSettings:
    """
    Настройки для ARQ воркера, использующие новую архитектуру зависимостей.
    Теперь большинство зависимостей для задач будут передаваться через ctx.
    """
    redis_settings = RedisSettings.from_dsn(REDIS_CACHE_URL)
    functions = TASKS
    cron_jobs = []
    
    # ctx будет содержать все основные зависимости, инжектированные через DI
    ctx = {}

    @staticmethod
    async def on_startup(ctx: dict):
        """
        Выполняется один раз при старте воркера.
        Инициализирует DI-контейнер и помещает основные зависимости в ctx.
        """
        logger.info("🔧 ARQ Worker startup: Инициализация DI-контейнера и контекста ARQ...")
        try:
            await initialize_di_container()
            
            # 🔥 ИЗМЕНЕНИЕ: Загружаем все необходимые зависимости через inject
            # и помещаем их в ctx.
            ctx["logger"] = inject.instance(logging.Logger)
            ctx["redis_reader"] = inject.instance(ReferenceDataReader)
            ctx["redis_batch_store"] = inject.instance(RedisBatchStore)
            
            # Фабрики репозиториев
            ctx["pg_location_repo_factory"] = inject.instance(Callable[[AsyncSession], IGameLocationRepository])
            ctx["equipment_template_repo_factory"] = inject.instance(Callable[[AsyncSession], IEquipmentTemplateRepository])
            ctx["character_pool_repo_factory"] = inject.instance(Callable[[AsyncSession], ICharacterPoolRepository])
            
            # Mongo репозитории (обычно не требуют сессии)
            ctx["mongo_world_repo"] = inject.instance(IWorldStateRepository)
            ctx["location_state_repo"] = inject.instance(ILocationStateRepository)

            # Экземпляры процессоров, если они инжектируются и не создаются прямо в задачах
            # (Если они инжектируются в задачи, то их не нужно помещать в ctx)
            # Если ItemBatchProcessor, CharacterBatchProcessor, WorldMapGenerator создаются внутри ARQ-задач,
            # и их зависимости (фабрики репозиториев, ридеры) берутся из ctx, то их самих не надо инжектировать здесь.
            # Если они были в autoparams ранее, значит, они инжектировались.
            # Для простоты, пока оставим как есть, предполагая, что ARQ-задачи будут создавать их.
            # Если впоследствии они должны инжектироваться как синглтоны, их можно добавить сюда.

            WorkerSettings.ctx.update(ctx)
            ctx["logger"].info("✅ ARQ Worker startup: DI-контейнер и основные зависимости успешно инициализированы и помещены в ctx.")

        except Exception as e:
            logger.critical(f"🚨 ARQ Worker startup: Критическая ошибка: {e}", exc_info=True)
            await WorkerSettings.on_shutdown(ctx) 
            raise

    @staticmethod
    async def on_job_start(ctx: dict):
        """
        Выполняется перед каждой задачей.
        Логика управления сессиями БД УДАЛЕНА, так как @transactional берет это на себя.
        """
        current_logger = ctx.get('logger', logging.getLogger(__name__))
        current_logger.debug(f"⚙️ ARQ Worker: Начало задачи {ctx.get('job_id')}.")
        # 🔥 ИЗМЕНЕНО: Удалена логика управления сессией БД
        # Убедитесь, что здесь нет кода, который открывает сессию
        # ctx["db_session_context"] = session_obj
        # ctx["db_session"] = await session_obj.__aenter__()

    @staticmethod
    async def on_job_end(ctx: dict):
        """
        Выполняется после каждой задачи.
        Логика закрытия сессий БД УДАЛЕНА.
        """
        current_logger = ctx.get('logger', logging.getLogger(__name__))
        current_logger.debug(f"⚙️ ARQ Worker: Завершение задачи {ctx.get('job_id')}.")
        # 🔥 ИЗМЕНЕНО: Удалена логика закрытия сессии БД
        # db_session_context = ctx.get("db_session_context")
        # if db_session_context:
        #     try:
        #         await db_session_context.__aexit__(None, None, None)
        #     except Exception as e:
        #         current_logger.error(f"❌ ARQ Worker: Ошибка при закрытии сессии БД: {e}", exc_info=True)

    @staticmethod
    async def run_periodic_task(ctx: dict):
        """Периодическая задача для выполнения фоновых операций."""
        # Поскольку ARQ-задачи теперь получают зависимости из ctx,
        # collect_and_dispatch_sessions, если она должна инжектироваться,
        # должна быть либо отдельно забинжена как синглтон, либо
        # получить свои зависимости через ctx, если она вызывается отсюда.
        # Для простоты пока оставим как было, предполагая, что collect_and_dispatch_sessions
        # сама разрешает свои зависимости через autoparams.
        from game_server.Logic.ApplicationLogic.world_orchestrator.workers.autosession_watcher.tick_AutoSession_Watcher import collect_and_dispatch_sessions
        
        periodic_task_instance = inject.instance(collect_and_dispatch_sessions)

        while True:
            try:
                ctx["logger"].info("⏱️ Запуск периодической задачи...")
                await periodic_task_instance()
                ctx["logger"].info("✅ Периодическая задача успешно выполнена.")
                await asyncio.sleep(config.settings.runtime.PERIODIC_TASK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                ctx["logger"].info("🛑 Периодическая задача отменена.")
                break
            except Exception as e:
                ctx["logger"].error(f"❌ Ошибка в периодической задаче: {e}", exc_info=True)
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
        
        await shutdown_di_container()
        
        logger.info("✅ ARQ Worker shutdown: Все зависимости корректно завершили работу.")