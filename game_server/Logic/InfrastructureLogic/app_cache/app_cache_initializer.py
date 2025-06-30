# game_server/Logic/InfrastructureLogic/app_cache/app_cache_initializer.py

import logging
from typing import Optional, Dict, Any

# Импортируем CentralRedisClient
from .central_redis_client import CentralRedisClient

# Импорт всех классов менеджеров
from .services.shard_count.shard_count_cache_manager import ShardCountCacheManager
from .services.task_queue.redis_batch_store import RedisBatchStore
# НОВОЕ: Импорт TaskQueueCacheManager

from .services.character.character_cache_manager import CharacterCacheManager
from .services.item.item_cache_manager import ItemCacheManager
from .services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from .services.reference_data.reference_data_reader import ReferenceDataReader
from .services.discord.backend_guild_config_manager import BackendGuildConfigManager
from .interfaces.interfaces_session_cache import ISessionManager
from .services.session.session_manager import RedisSessionManager

# Импортируем настройки Redis
from game_server.config.settings_core import REDIS_URL, REDIS_POOL_SIZE, REDIS_PASSWORD

# Импортируем геттер для RepositoryManager, так как он является зависимостью
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import get_repository_manager_instance
from game_server.config.logging.logging_setup import app_logger as logger

# Глобальные переменные модуля
central_redis_client_instance: Optional[CentralRedisClient] = None
_initialized_managers: Dict[str, Any] = {}


async def initialize_app_cache_managers() -> bool:
    """
    Инициализирует все менеджеры кэша. Теперь он сам импортирует нужные зависимости,
    когда они требуются (через get_repository_manager_instance).
    """
    global central_redis_client_instance

    # Проверяем, чтобы не было повторной инициализации
    if _initialized_managers:
        logger.warning("Менеджеры кэша уже инициализированы. Пропуск.")
        return True

    logger.info("🔧 Инициализация всех менеджеров кэша и Redis-сервисов...")

    try:
        # 1. Инициализация CentralRedisClient
        logger.info("🔧 Подключение CentralRedisClient...")
        central_redis_client_instance = CentralRedisClient(
            redis_url=REDIS_URL,
            max_connections=REDIS_POOL_SIZE,
            redis_password=REDIS_PASSWORD
        )
        await central_redis_client_instance.connect()
        logger.info("✅ CentralRedisClient успешно инициализирован.")
        _initialized_managers["central_redis_client"] = central_redis_client_instance

        if not hasattr(central_redis_client_instance, 'hgetall_msgpack'):
            logger.critical("DEBUG: !!! CENTRAL_REDIS_CLIENT НЕ ИМЕЕТ hgetall_msgpack ПРИ ИНИЦИАЛИЗАЦИИ CACHE MANAGERS !!!")
            raise AttributeError(f"DEBUG: Global CentralRedisClient from module '{central_redis_client_instance.__class__.__module__}' has no attribute 'hgetall_msgpack'")
        logger.critical("--- DEBUG: CentralRedisClient Проверка завершена ---")
        # 🔥🔥🔥 КОНЕЦ ОТЛАДОЧНОГО КОДА В initialize_app_cache_managers 🔥🔥🔥


        # 2. Инициализация остальных менеджеров, которые зависят только от Redis
        _initialized_managers["redis_batch_store"] = RedisBatchStore(redis_client=central_redis_client_instance)
        # НОВОЕ: Инициализация TaskQueueCacheManager
        _initialized_managers["character_cache_manager"] = CharacterCacheManager(redis_client=central_redis_client_instance)
        _initialized_managers["item_cache_manager"] = ItemCacheManager(redis_client=central_redis_client_instance)
        _initialized_managers["reference_data_reader"] = ReferenceDataReader(redis_client=central_redis_client_instance)
        _initialized_managers["shard_count_cache_manager"] = ShardCountCacheManager(redis_client=central_redis_client_instance)
        _initialized_managers["session_manager"] = RedisSessionManager(redis_client=central_redis_client_instance)
        _initialized_managers["backend_guild_config_manager"] = BackendGuildConfigManager(redis_client=central_redis_client_instance)
        logger.info("✅ Базовые менеджеры кэша инициализированы.")
        
        # 3. Инициализация менеджеров, у которых есть дополнительные зависимости
        logger.info("🔧 Инициализация ReferenceDataCacheManager...")
        repository_manager = get_repository_manager_instance()
        _initialized_managers["reference_data_cache_manager"] = ReferenceDataCacheManager(
            repository_manager=repository_manager,
            redis_client=central_redis_client_instance
        )
        logger.info("✅ ReferenceDataCacheManager инициализирован.")
        
        logger.info("✅ Все менеджеры кэша и Redis-сервисов успешно инициализированы.")
        return True
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации менеджеров кэша: {e}", exc_info=True)
        if central_redis_client_instance:
            await central_redis_client_instance.close()
            logger.warning("CentralRedisClient закрыт после ошибки инициализации менеджеров.")
        return False


def get_initialized_app_cache_managers() -> Dict[str, Any]:
    if not _initialized_managers:
        logger.error("🚫 Менеджеры кэша не инициализированы. Вызовите initialize_app_cache_managers() сначала.")
        raise RuntimeError("App cache managers are not initialized.")
    return _initialized_managers


def get_redis_client() -> CentralRedisClient:
    if central_redis_client_instance is None:
        raise RuntimeError("Redis client is not initialized. Ensure lifespan startup event has run.")
    return central_redis_client_instance


async def shutdown_app_cache_managers() -> None:
    global central_redis_client_instance
    global _initialized_managers

    logger.info("🛑 Завершение работы менеджеров кэша и Redis-сервисов...")
    if central_redis_client_instance:
        await central_redis_client_instance.close()
    
    central_redis_client_instance = None
    _initialized_managers = {}
    logger.info("✅ Завершение работы менеджеров кэша выполнено.")

    
def get_session_manager_instance() -> ISessionManager:
    """
    Возвращает инициализированный экземпляр RedisSessionManager.
    """
    try:
        return _initialized_managers["session_manager"]
    except KeyError:
        logger.error("🚫 RedisSessionManager не инициализирован. Вызовите initialize_app_cache_managers() сначала.")
        raise RuntimeError("RedisSessionManager is not initialized.")
