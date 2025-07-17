import logging
import time
from typing import Dict, Any, Optional # Добавил Optional

# 🔥 ИЗМЕНЕНИЕ: Импортируем интерфейсы конкретных репозиториев, которые могут быть нужны
# (Это ПРИМЕР, нужно будет определить, какие именно репозитории нужны collect_and_dispatch_sessions)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository # Пример
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository # Пример

from game_server.Logic.ApplicationLogic.world_orchestrator.workers.autosession_watcher.tick_AutoSession_Watcher import collect_and_dispatch_sessions
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus # Предполагается, что это ваш message_bus

logger = logging.getLogger(__name__)

# ==============================================================================
# Основная функция для выполнения периодической задачи
# ==============================================================================
async def execute_periodic_task(
    # 🔥 ИЗМЕНЕНИЕ: Теперь ожидаем конкретные репозитории вместо RepositoryManager
    # Здесь нужно указать ТОЧНЫЕ репозитории, которые нужны collect_and_dispatch_sessions.
    # Это пример:
    auto_session_repo: IAutoSessionRepository,
    xp_tick_data_repo: IXpTickDataRepository, 
    
    message_bus: RedisMessageBus,
    app_managers: Dict[str, Any], # Receives dictionary with all managers
):
    """
    Основная функция для выполнения периодической задачи.
    Получает необходимые зависимости.
    """
    start_time = time.time()
    logger.info(f"🚀 Запуск периодической задачи обработки тиков...")

    try:
        await collect_and_dispatch_sessions(
            # 🔥 ИЗМЕНЕНИЕ: Передаем конкретные репозитории вместо repository_manager
            auto_session_repo=auto_session_repo, # Passed down
            xp_tick_data_repo=xp_tick_data_repo, # Passed down                       
            message_bus=message_bus, # Passed down
            app_cache_managers=app_managers, # Passed down
        )
        duration = time.time() - start_time
        logger.info(f"🏁 Периодическая задача успешно завершена. Длительность: {duration:.2f} сек.")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении периодической задачи: {e}", exc_info=True)
        return False