# game_server/core/dependency_aggregator.py

from typing import Dict, Any, Coroutine
from game_server.config.logging.logging_setup import app_logger as logger

# 1. Импортируем все низкоуровневые инициализаторы и геттеры
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import arq_pool_manager
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import (
    initialize_app_post_managers, 
    get_repository_manager_instance, 
    shutdown_app_post_managers
)
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import (
    initialize_app_cache_managers, 
    get_initialized_app_cache_managers, 
    shutdown_app_cache_managers
)
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.Logic.InfrastructureLogic.db_instance import engine

# 2. Создаем "склад" для хранения готовых экземпляров зависимостей
_global_dependencies_instance: Dict[str, Any] = {}

async def initialize_all_dependencies() -> None:
    """
    Вызывает все низкоуровневые инициализаторы и сохраняет
    каждый созданный экземпляр в глобальный словарь _global_dependencies_instance.
    Эта функция вызывается один раз при старте приложения.
    """
    global _global_dependencies_instance
    if _global_dependencies_instance:
        logger.warning("Попытка повторной инициализации глобальных зависимостей.")
        return

    logger.info("--- 🚀 НАЧАЛО ИНИЦИАЛИЗАЦИИ ВСЕХ ИНФРАСТРУКТУРНЫХ ЗАВИСИМОСТЕЙ ---")
    
    # PostgreSQL
    if not await initialize_app_post_managers():
        raise RuntimeError("Ошибка инициализации PostgreSQL.")
    _global_dependencies_instance["repository_manager"] = get_repository_manager_instance()
    
    # Redis Cache
    if not await initialize_app_cache_managers():
        raise RuntimeError("Ошибка инициализации Cache Managers.")
    
    cache_managers = get_initialized_app_cache_managers()
    
    # <<< ИСПРАВЛЕНО: Создаем ключ 'app_cache_managers' для обратной совместимости
    _global_dependencies_instance["app_cache_managers"] = cache_managers
    
    # <<< ИСПРАВЛЕНО: Также добавляем каждый менеджер на верхний уровень для прямого доступа
    _global_dependencies_instance.update(cache_managers)
    
    # ARQ
    await arq_pool_manager.startup()
    _global_dependencies_instance["arq_redis_pool"] = arq_pool_manager.arq_redis_pool
    
    # RabbitMQ
    rabbit_bus = RabbitMQMessageBus()
    await rabbit_bus.connect()
    _global_dependencies_instance["message_bus"] = rabbit_bus
    
    # Logger
    _global_dependencies_instance["logger"] = logger
    
    logger.info("--- ✅ ВСЕ ИНФРАСТРУКТУРНЫЕ ЗАВИСИМОСТИ УСПЕШНО ИНИЦИАЛИЗИРОВАНЫ И СОХРАНЕНЫ ---")

def get_global_dependencies() -> Dict[str, Any]:
    """Возвращает словарь со всеми инициализированными глобальными зависимостями."""
    return _global_dependencies_instance

async def shutdown_all_dependencies() -> None:
    """Корректно останавливает все инфраструктурные зависимости."""
    logger.info("--- 🛑 НАЧАЛО ОСТАНОВКИ ВСЕХ ИНФРАСТРУКТУРНЫХ ЗАВИСИМОСТЕЙ ---")
    
    # Остановка в обратном порядке
    if "message_bus" in _global_dependencies_instance:
        await _global_dependencies_instance["message_bus"].close()
        
    if "arq_redis_pool" in _global_dependencies_instance:
        await arq_pool_manager.shutdown()
        
    await shutdown_app_cache_managers()
    await shutdown_app_post_managers()
    
    if engine:
        await engine.dispose()
        
    logger.info("--- ✅ ВСЕ ИНФРАСТРУКТУРНЫЕ ЗАВИСИМОСТИ КОРРЕКТНО ОСТАНОВЛЕНЫ ---")
