import logging
import asyncio
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession # Оставляем, так как db_session передается
from arq import ArqRedis # Оставляем для ctx['redis']

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ИМПОРТ ИНТЕРФЕЙСОВ для менеджеров (для типизации)
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager # ИЗМЕНЕНО
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient # ИЗМЕНЕНО
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader # ИЗМЕНЕНО

# ДОБАВЛЕНО: Импорт RepositoryManager для доступа к БД
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # ДОБАВЛЕНО

from game_server.config.provider import config


async def arq_process_exploration_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    log_prefix = f"EXPLORATION_TASK_ID({batch_id}):"
    logger.info(f"✅ [WORKER] Получена ARQ-задача на ИССЛЕДОВАНИЕ. Batch ID: {batch_id}. Имитация работы...")
    
    # Извлечение зависимостей из контекста ARQ
    app_managers = ctx.get('app_managers')
    arq_redis_pool: ArqRedis = ctx['redis']
    db_session: AsyncSession = ctx['db_session'] # db_session все еще передается для совместимости
    repository_manager: RepositoryManager = ctx['repository_manager'] # ДОБАВЛЕНО: Получаем RepositoryManager

    if not app_managers:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: 'app_managers' не найден в контексте ARQ воркера.")
        raise RuntimeError("'app_managers' not initialized in ARQ worker context.")

    task_queue_cache_manager: ITaskQueueCacheManager = app_managers.get('task_queue_cache_manager')
    central_redis_client: CentralRedisClient = app_managers.get('central_redis_client')
    reference_data_reader: IReferenceDataReader = app_managers.get('reference_data_reader')

    if (
        task_queue_cache_manager is None or
        central_redis_client is None or
        reference_data_reader is None or
        repository_manager is None # ДОБАВЛЕНО
    ):
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Один или несколько менеджеров приложения (из app_managers/ctx) не инициализированы или не переданы в ARQ-контекст!")
        raise RuntimeError("Required app managers are None in ARQ worker context.")

    # Здесь будет ваша реальная логика, использующая эти менеджеры
    # Например, вызов некоторого сервиса DomainLogic:
    # from game_server.Logic.DomainLogic.some_exploration_logic import ExplorationService
    # exploration_service = ExplorationService(repository_manager=repository_manager, app_cache_managers=app_managers)
    # await exploration_service.process_exploration_data(batch_id)

    await asyncio.sleep(1) # Имитация работы
    logger.info(f"🏁 [WORKER] ARQ-задача на ИССЛЕДОВАНИЕ (Batch ID: {batch_id}) завершена.")

async def arq_process_training_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    log_prefix = f"TRAINING_TASK_ID({batch_id}):"
    logger.info(f"✅ [WORKER] Получена ARQ-задача на ТРЕНИРОВКУ. Batch ID: {batch_id}. Имитация работы...")
    
    # Извлечение зависимостей из контекста ARQ
    app_managers = ctx.get('app_managers')
    arq_redis_pool: ArqRedis = ctx['redis']
    db_session: AsyncSession = ctx['db_session'] # db_session все еще передается для совместимости
    repository_manager: RepositoryManager = ctx['repository_manager'] # ДОБАВЛЕНО: Получаем RepositoryManager

    if not app_managers:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: 'app_managers' не найден в контексте ARQ воркера.")
        raise RuntimeError("'app_managers' not initialized in ARQ worker context.")

    task_queue_cache_manager: ITaskQueueCacheManager = app_managers.get('task_queue_cache_manager')
    central_redis_client: CentralRedisClient = app_managers.get('central_redis_client')
    reference_data_reader: IReferenceDataReader = app_managers.get('reference_data_reader')

    if (
        task_queue_cache_manager is None or
        central_redis_client is None or
        reference_data_reader is None or
        repository_manager is None # ДОБАВЛЕНО
    ):
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Один или несколько менеджеров приложения (из app_managers/ctx) не инициализированы или не переданы в ARQ-контекст!")
        raise RuntimeError("Required app managers are None in ARQ worker context.")

    # Здесь будет ваша реальная логика, использующая эти менеджеры
    # from game_server.Logic.DomainLogic.some_training_logic import TrainingService
    # training_service = TrainingService(repository_manager=repository_manager, app_cache_managers=app_managers)
    # await training_service.process_training_data(batch_id)

    await asyncio.sleep(1) # Имитация работы
    logger.info(f"🏁 [WORKER] ARQ-задача на ТРЕНИРОВКУ (Batch ID: {batch_id}) завершена.")

async def arq_process_crafting_task(
    ctx: Dict[str, Any],
    batch_id: str
) -> None:
    log_prefix = f"CRAFTING_TASK_ID({batch_id}):"
    logger.info(f"✅ [WORKER] Получена ARQ-задача на КРАФТ. Batch ID: {batch_id}. Имитация работы...")
    
    # Извлечение зависимостей из контекста ARQ
    app_managers = ctx.get('app_managers')
    arq_redis_pool: ArqRedis = ctx['redis']
    db_session: AsyncSession = ctx['db_session'] # db_session все еще передается для совместимости
    repository_manager: RepositoryManager = ctx['repository_manager'] # ДОБАВЛЕНО: Получаем RepositoryManager

    if not app_managers:
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: 'app_managers' не найден в контексте ARQ воркера.")
        raise RuntimeError("'app_managers' not initialized in ARQ worker context.")

    task_queue_cache_manager: ITaskQueueCacheManager = app_managers.get('task_queue_cache_manager')
    central_redis_client: CentralRedisClient = app_managers.get('central_redis_client')
    reference_data_reader: IReferenceDataReader = app_managers.get('reference_data_reader')
    
    if (
        task_queue_cache_manager is None or
        central_redis_client is None or
        reference_data_reader is None or
        repository_manager is None # ДОБАВЛЕНО
    ):
        logger.critical(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Один или несколько менеджеров приложения (из app_managers/ctx) не инициализированы или не переданы в ARQ-контекст!")
        raise RuntimeError("Required app managers are None in ARQ worker context.")

    # Здесь будет ваша реальная логика, использующая эти менеджеры
    # from game_server.Logic.DomainLogic.some_crafting_logic import CraftingService
    # crafting_service = CraftingService(repository_manager=repository_manager, app_cache_managers=app_managers)
    # await crafting_service.process_crafting_data(batch_id)

    await asyncio.sleep(1) # Имитация работы
    logger.info(f"🏁 [WORKER] ARQ-задача на КРАФТ (Batch ID: {batch_id}) завершена.")