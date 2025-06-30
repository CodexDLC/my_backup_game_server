# game_server/Logic/CoreServices/core_services_initializer.py

import logging
from typing import Optional, Dict, Any

# Импортируем зависимость - RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import get_repository_manager_instance

# Импортируем все сервисы, которыми будет управлять этот инициализатор
from .services.identifiers_servise import IdentifiersServise
from .services.random_service import RandomService # <-- ДОБАВЛЯЕМ ИМПОРТ

logger = logging.getLogger(__name__)

_initialized_core_services: Dict[str, Any] = {}

def initialize_core_services() -> bool:
    """
    Инициализирует все сервисы из CoreServices и сохраняет их во внутренний словарь.
    """
    global _initialized_core_services
    logger.info("🔧 Инициализация Core-сервисов...")
    
    try:
        if _initialized_core_services:
            logger.warning("Core-сервисы уже инициализированы. Пропуск.")
            return True
            
        repo_manager = get_repository_manager_instance()
        
        # Инициализируем каждый сервис и складываем в словарь
        _initialized_core_services["identifiers_service"] = IdentifiersServise(repository_manager=repo_manager)
        logger.info("✅ IdentifiersServise инициализирован.")
        
        # ДОБАВЛЕНО: Инициализация RandomService
        _initialized_core_services["random_service"] = RandomService()
        logger.info("✅ RandomService инициализирован.")

        logger.info("✅ Все Core-сервисы успешно инициализированы.")
        return True
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации Core-сервисов: {e}", exc_info=True)
        return False

def get_identifiers_service_instance() -> IdentifiersServise:
    """
    Возвращает инициализированный экземпляр IdentifiersServise.
    """
    try:
        return _initialized_core_services["identifiers_service"]
    except KeyError:
        logger.error("🚫 IdentifiersServise не инициализирован. Вызовите initialize_core_services() сначала.")
        raise RuntimeError("IdentifiersServise is not initialized.")
    
def get_random_service_instance() -> RandomService:
    """
    Возвращает инициализированный экземпляр RandomService.
    """
    try:
        return _initialized_core_services["random_service"]
    except KeyError:
        logger.error("🚫 RandomService не инициализирован. Вызовите initialize_core_services() сначала.")
        raise RuntimeError("RandomService is not initialized.")