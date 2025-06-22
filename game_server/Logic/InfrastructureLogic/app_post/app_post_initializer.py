# game_server/Logic/InfrastructureLogic/app_post/app_post_initializer.py

import logging
from typing import Optional, Callable, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession # Для async_session_factory

from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
# Импорты ваших репозиториев (если они нужны здесь для инициализации)
# from .repository_groups.<domain>.<repo_impl> import <RepoImpl>


logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра RepositoryManager
# Она должна быть Optional, так как сначала она None
_repository_manager_instance: Optional[RepositoryManager] = None

async def initialize_app_post_managers(async_session_factory: Callable[[], AsyncSession]) -> bool:
    """
    Инициализирует RepositoryManager и все его репозитории.
    Должен быть вызван один раз при старте приложения.
    """
    global _repository_manager_instance # Объявляем, что будем изменять глобальную переменную

    logger.info("🔧 Инициализация менеджеров PostgreSQL (RepositoryManager)...")

    try:
        if _repository_manager_instance is None:
            _repository_manager_instance = RepositoryManager(db_session_factory=async_session_factory)
            # Здесь можно добавить любые дополнительные проверки или действия после инициализации,
            # например, проверку подключения к БД через RepositoryManager
            logger.info("✅ RepositoryManager успешно инициализирован.")
        else:
            logger.warning("RepositoryManager уже инициализирован. Пропуск повторной инициализации.")
        return True
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации RepositoryManager: {e}", exc_info=True)
        # Если инициализация не удалась, обнуляем экземпляр
        _repository_manager_instance = None
        return False

def get_repository_manager_instance() -> RepositoryManager:
    """
    Возвращает инициализированный экземпляр RepositoryManager.
    Должна быть вызвана ТОЛЬКО после initialize_app_post_managers().
    """
    if _repository_manager_instance is None:
        logger.error("🚫 RepositoryManager не инициализирован. Вызовите initialize_app_post_managers() сначала.")
        raise RuntimeError("RepositoryManager is not initialized.")
    return _repository_manager_instance

async def shutdown_app_post_managers() -> None:
    """
    Корректно закрывает ресурсы, связанные с PostgreSQL.
    В данном случае, если RepositoryManager управляет пулом соединений или Engine,
    логика закрытия должна быть в нем или здесь.
    """
    global _repository_manager_instance

    logger.info("🛑 Завершение работы менеджеров PostgreSQL...")
    # Если RepositoryManager сам имеет метод close/dispose для ресурсов БД, вызовите его
    # if _repository_manager_instance and hasattr(_repository_manager_instance, 'close'):
    #     await _repository_manager_instance.close()
    
    # В данном случае, закрытие движка SQLAlchemy происходит в game_world_state_orchestrator.py
    # через 'engine.dispose()', поэтому здесь прямое закрытие не нужно,
    # но _repository_manager_instance все равно обнуляем.
    
    _repository_manager_instance = None
    logger.info("✅ Менеджеры PostgreSQL завершены.")