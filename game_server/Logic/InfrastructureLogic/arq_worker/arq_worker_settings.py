# game_server/Logic/InfrastructureLogic/arq_worker/arq_worker_settings.py

import asyncio
import logging
from arq.connections import RedisSettings
from typing import Dict, Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession 

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_dinamic_location_manager import IDynamicLocationManager
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
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
        Инициализирует DI-контейнер и помещает основные зависимости в ctx.
        """
        logger.info("🔧 ARQ Worker startup: Инициализация DI-контейнера и контекста ARQ...")
        try:
            await initialize_di_container()
            
            # Загружаем все необходимые зависимости через inject и помещаем их в ctx.
            ctx["logger"] = inject.instance(logging.Logger)
            ctx["redis_reader"] = inject.instance(ReferenceDataReader)
            ctx["redis_batch_store"] = inject.instance(RedisBatchStore)
            
            # Фабрики репозиториев
            ctx["pg_location_repo_factory"] = inject.instance(Callable[[AsyncSession], IGameLocationRepository])
            ctx["equipment_template_repo_factory"] = inject.instance(Callable[[AsyncSession], IEquipmentTemplateRepository])
            ctx["character_pool_repo_factory"] = inject.instance(Callable[[AsyncSession], ICharacterPoolRepository])
            
            # Mongo репозитории
            ctx["mongo_world_repo"] = inject.instance(IWorldStateRepository)
            ctx["location_state_repo"] = inject.instance(ILocationStateRepository)

            # ✅ НОВЫЕ ЗАВИСИМОСТИ для задачи aggregate_location_state
            ctx["dynamic_location_manager"] = inject.instance(IDynamicLocationManager)
            ctx["message_bus"] = inject.instance(IMessageBus)
            
            WorkerSettings.ctx.update(ctx)
            ctx["logger"].info("✅ ARQ Worker startup: DI-контейнер и зависимости успешно инициализированы.")

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


    @staticmethod
    async def on_job_end(ctx: dict):
        """
        Выполняется после каждой задачи.
        Логика закрытия сессий БД УДАЛЕНА.
        """
        current_logger = ctx.get('logger', logging.getLogger(__name__))
        current_logger.debug(f"⚙️ ARQ Worker: Завершение задачи {ctx.get('job_id')}.")

    @staticmethod
    async def run_periodic_task(ctx: dict):
        """Периодическая задача для выполнения фоновых операций."""
        
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