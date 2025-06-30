# game_server/Logic/InfrastructureLogic/app_post/app_post_initializer.py

import logging
from typing import Optional

# ИЗМЕНЕНО: Мы импортируем фабрику сессий напрямую здесь


from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.config.logging.logging_setup import app_logger as logger


# Глобальная переменная для хранения единственного экземпляра RepositoryManager
_repository_manager_instance: Optional[RepositoryManager] = None

# ИЗМЕНЕНО: Функция больше не принимает аргументов
async def initialize_app_post_managers() -> bool:
    """
    Инициализирует RepositoryManager. Теперь он сам импортирует фабрику сессий.
    Должен быть вызван один раз при старте приложения.
    """
    global _repository_manager_instance

    logger.info("🔧 Инициализация менеджеров PostgreSQL (RepositoryManager)...")

    try:
        if _repository_manager_instance is None:
            # ИЗМЕНЕНО: Используем импортированный AsyncSessionLocal напрямую
            _repository_manager_instance = RepositoryManager(db_session_factory=AsyncSessionLocal)
            
            logger.info("✅ RepositoryManager успешно инициализирован.")
        else:
            logger.warning("RepositoryManager уже инициализирован. Пропуск повторной инициализации.")
        return True
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации RepositoryManager: {e}", exc_info=True)
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
    Обнуляет экземпляр менеджера при завершении работы.
    """
    global _repository_manager_instance
    logger.info("🛑 Завершение работы менеджеров PostgreSQL...")
    _repository_manager_instance = None
    logger.info("✅ Менеджеры PostgreSQL завершены.")