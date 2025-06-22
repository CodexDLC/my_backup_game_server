import logging
from typing import Optional, Callable, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт CentralRedisClient
from .central_redis_client import CentralRedisClient

# Импорт всех классов менеджеров из их новых местоположений
from .services.shard_count.shard_count_cache_manager import ShardCountCacheManager # Обновлен путь
from .services.task_queue.redis_batch_store import RedisBatchStore # Обновлен путь
from .services.task_queue.task_queue_cache_manager import TaskQueueCacheManager # Обновлен путь
from .services.character.character_cache_manager import CharacterCacheManager # Обновлен путь
from .services.item.item_cache_manager import ItemCacheManager # Обновлен путь
# ИЗМЕНЕНО: Исправлен путь импорта ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager # Обновлен путь
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader # Обновлен путь
from .services.tick.tick_cache_manager import TickCacheManager # Обновлен путь

# Импортируем настройки Redis
from game_server.config.settings_core import REDIS_URL, REDIS_POOL_SIZE, REDIS_PASSWORD

# ДОБАВЛЕНО: Импорт get_repository_manager_instance
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import get_repository_manager_instance #


logger = logging.getLogger(__name__)

central_redis_client_instance: Optional[CentralRedisClient] = None

_initialized_managers: Dict[str, Any] = {}

async def initialize_app_cache_managers(async_session_factory: Callable[[], AsyncSession]) -> bool:
    """
    Инициализирует все менеджеры кэша и Redis-сервисов и сохраняет их во внутренний словарь.
    Должен быть вызван один раз при старте приложения.
    """
    global central_redis_client_instance

    logger.info("🔧 Инициализация всех менеджеров кэша и Redis-сервисов...")

    try:
        # 1. Инициализация CentralRedisClient (DB 0)
        logger.info("🔧 Подключение CentralRedisClient к DB 0...")
        central_redis_client_instance = CentralRedisClient(
            redis_url=REDIS_URL,
            max_connections=REDIS_POOL_SIZE,
            redis_password=REDIS_PASSWORD
        )
        await central_redis_client_instance.connect()
        logger.info("✅ CentralRedisClient успешно инициализирован и подключен к DB 0.")
        _initialized_managers["central_redis_client"] = central_redis_client_instance

        # 2. Инициализация RedisBatchStore
        _initialized_managers["redis_batch_store"] = RedisBatchStore(redis_client=central_redis_client_instance)
        logger.info("✅ RedisBatchStore инициализирован.")

        # 3. Инициализация TaskQueueCacheManager
        _initialized_managers["task_queue_cache_manager"] = TaskQueueCacheManager(redis_client=central_redis_client_instance)
        logger.info("✅ TaskQueueCacheManager инициализирован.")

        # 4. Инициализация CharacterCacheManager
        _initialized_managers["character_cache_manager"] = CharacterCacheManager(redis_client=central_redis_client_instance)
        logger.info("✅ CharacterCacheManager инициализирован.")

        # 5. Инициализация ItemCacheManager
        _initialized_managers["item_cache_manager"] = ItemCacheManager(redis_client=central_redis_client_instance)
        logger.info("✅ ItemCacheManager инициализирован.")

        # 6. Инициализация ReferenceDataCacheManager
        logger.info("🔧 Инициализация ReferenceDataCacheManager...")
        # ДОБАВЛЕНО: Получаем RepositoryManager
        repository_manager = get_repository_manager_instance() # <--- ДОБАВЛЕНО
        _initialized_managers["reference_data_cache_manager"] = ReferenceDataCacheManager(
            repository_manager=repository_manager, # <--- ИЗМЕНЕНО: Передаем repository_manager
            redis_client=central_redis_client_instance
        )
        logger.info("✅ ReferenceDataCacheManager инициализирован.")

        # 7. Инициализация ReferenceDataReader
        _initialized_managers["reference_data_reader"] = ReferenceDataReader(redis_client=central_redis_client_instance)
        logger.info("✅ ReferenceDataReader инициализирован.")

        # 8. Инициализация TickCacheManager
        _initialized_managers["tick_cache_manager"] = TickCacheManager(redis_client=central_redis_client_instance)
        logger.info("✅ TickCacheManager инициализирован.")

        # 9. Инициализация ShardCountCacheManager
        _initialized_managers["shard_count_cache_manager"] = ShardCountCacheManager(redis_client=central_redis_client_instance)
        logger.info("✅ ShardCountCacheManager инициализирован.")

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

def get_redis_client() -> "CentralRedisClient":
    if central_redis_client_instance is None:
        raise RuntimeError("Redis client is not initialized. Ensure lifespan startup event has run.")
    return central_redis_client_instance

async def shutdown_app_cache_managers() -> None:
    global central_redis_client_instance
    logger.info("🛑 Завершение работы менеджеров кэша и Redis-сервисов...")
    if central_redis_client_instance:
        await central_redis_client_instance.close()
        logger.info("✅ CentralRedisClient закрыт.")
    else:
        logger.debug("CentralRedisClient не был инициализирован или уже закрыт.")
    logger.info("✅ Завершение работы менеджеров кэша выполнено.")