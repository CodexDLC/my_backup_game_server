import logging
import time
# from sqlalchemy.ext.asyncio import AsyncSession # REMOVED: No longer needed here directly
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus
from game_server.config.logging.logging_setup import app_logger as logger

# Импортируем нашу основную функцию-оркестратор
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.auto_tick_module.tick_AutoSession_Watcher import collect_and_dispatch_sessions

# 🔥 НОВОЕ: Если collect_and_dispatch_sessions или его зависимости
# нуждаются в других менеджерах, добавляем их здесь.
# Предполагаем, что app_managers передается в run_periodic_task в arq_worker_settings.py
from typing import Dict, Any # Для типизации app_managers, если будет использоваться

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager


# ==============================================================================
# Основная функция для выполнения периодической задачи
# ==============================================================================
async def execute_periodic_task(
    # db_session: AsyncSession, # REMOVED: No longer received directly
    repository_manager: RepositoryManager, # ADDED: Receives RepositoryManager
    message_bus: RedisMessageBus,
    app_managers: Dict[str, Any], # Receives dictionary with all managers
):
    """
    Основная функция для выполнения периодической задачи.
    Получает необходимые зависимости.
    """
    start_time = time.time()
    logger.info(f"🚀 Запуск периодической задачи обработки тиков...")

    # Извлекаем дополнительные менеджеры из app_managers, если collect_and_dispatch_sessions их использует
    # Например:
    # task_queue_cache_manager = app_managers.get('task_queue_cache_manager')
    # central_redis_client = app_managers.get('central_redis_client')
    # reference_data_reader = app_managers.get('reference_data_reader')

    try:
        await collect_and_dispatch_sessions(
            repository_manager=repository_manager, # Passed down
            message_bus=message_bus, # Passed down
            app_cache_managers=app_managers, # Passed down
        )
        duration = time.time() - start_time
        logger.info(f"🏁 Периодическая задача успешно завершена. Длительность: {duration:.2f} сек.")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении периодической задачи: {e}", exc_info=True)
        return False