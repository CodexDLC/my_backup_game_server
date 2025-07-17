# game_server/core/di_modules/di_container.py

import logging
from typing import Dict, Any, Type, Callable

import inject
# 🔥 ИЗМЕНЕНО: Импортируем AsyncIOMotorClient, УДАЛЕН импорт MongoClient из pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

# --- Импорты инициализаторов и функций shutdown ---
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import shutdown_app_cache_managers
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_mongo.app_mongo_initializer import initialize_mongo_repositories
# --- Импорты из инфраструктуры ---
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal, engine
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
# Импорт логгера
from game_server.config.logging.logging_setup import app_logger as global_app_logger
from game_server.config.provider import config
from game_server.core.di_modules.auth_bindings import configure_auth_services
from game_server.core.di_modules.cache_bindings import configure_cache_managers
from game_server.core.di_modules.core_service_bindings import configure_core_services
from game_server.core.di_modules.mongo_bindings import configure_mongo_repositories
# --- Импорты модулей биндинга ---
from game_server.core.di_modules.postgres_bindings import configure_postgres_repositories
from game_server.core.di_modules.system_service_bindings import configure_system_services
from game_server.core.di_modules.world_orchestrator_bindings import configure_world_orchestrators

logger = logging.getLogger(__name__)

_async_singletons_instances: Dict[Type | str, Any] = {}

def configure_dependencies(binder):
    logger.info("🔧 Конфигурирование DI-контейнера...")
    binder.bind(logging.Logger, global_app_logger)
    binder.bind(IMessageBus, _async_singletons_instances[RabbitMQMessageBus])
    binder.bind(CentralRedisClient, _async_singletons_instances[CentralRedisClient])
    
    # 🔥 ИЗМЕНЕНО: Биндим AsyncIOMotorClient, а не MongoClient (который синхронный)
    binder.bind(AsyncIOMotorClient, _async_singletons_instances[AsyncIOMotorClient]) 
    binder.bind('mongo_database_obj', _async_singletons_instances['mongo_database_obj'])
    binder.bind(AsyncIOMotorDatabase, _async_singletons_instances['mongo_database_obj']) # Биндим по типу AsyncIOMotorDatabase
    
    # Биндим фабрику сессий SQLAlchemy AsyncSessionLocal к типу Callable[[], AsyncSession]
    binder.bind(Callable[[], AsyncSession], AsyncSessionLocal)
    
    configure_postgres_repositories(binder)
    configure_mongo_repositories(binder)
    configure_cache_managers(binder)
    configure_core_services(binder)
    configure_auth_services(binder)
    configure_system_services(binder)
    configure_world_orchestrators(binder)
    logger.info("✅ DI-контейнер сконфигурирован.")

async def initialize_di_container():
    logger.info("🔧 Инициализация DI-контейнера...")
    rabbit_bus = RabbitMQMessageBus()
    await rabbit_bus.connect()
    _async_singletons_instances[RabbitMQMessageBus] = rabbit_bus

    central_redis_client_instance = CentralRedisClient(
        redis_url=config.settings.core.REDIS_URL,
        max_connections=config.settings.core.REDIS_POOL_SIZE,
        redis_password=config.settings.core.REDIS_PASSWORD
    )
    await central_redis_client_instance.connect()
    _async_singletons_instances[CentralRedisClient] = central_redis_client_instance

    # 🔥 ИЗМЕНЕНО: Инициализация MongoDB клиента с AsyncIOMotorClient
    mongo_client_instance = AsyncIOMotorClient(config.settings.core.MONGO_URI) # <--- ВОТ ГДЕ ОШИБКА БЫЛА!
    _async_singletons_instances[AsyncIOMotorClient] = mongo_client_instance # Привязываем инстанс AsyncIOMotorClient
    mongo_db_instance = mongo_client_instance.get_database(config.settings.core.MONGO_DB_NAME) # Получаем объект базы данных
    _async_singletons_instances['mongo_database_obj'] = mongo_db_instance # Привязываем объект базы данных
    
    await initialize_mongo_repositories() 


    inject.configure(configure_dependencies)
    logger.info("✅ DI-контейнер успешно инициализирован.")

async def shutdown_di_container():
    logger.info("🛑 Завершение работы DI-контейнера...")
    try:
        if inject.is_configured():
            if RabbitMQMessageBus in _async_singletons_instances:
                rabbit_bus_instance = _async_singletons_instances[RabbitMQMessageBus]
                if hasattr(rabbit_bus_instance, 'close') and callable(rabbit_bus_instance.close):
                    await rabbit_bus_instance.close()
                    logger.info("RabbitMQ Message Bus закрыт.")
            
            await shutdown_app_cache_managers()
            logger.info("Менеджеры кэша приложений закрыты.")
            
            if 'arq_redis_pool_obj' in _async_singletons_instances:
                arq_pool = _async_singletons_instances['arq_redis_pool_obj']
                if arq_pool and hasattr(arq_pool, 'close') and callable(arq_pool.close):
                    await arq_pool.close()
                    logger.info("ARQ Redis Pool закрыт.")
            
            if CentralRedisClient in _async_singletons_instances:
                redis_client_instance = _async_singletons_instances[CentralRedisClient]
                if hasattr(redis_client_instance, 'close') and callable(redis_client_instance.close):
                    await redis_client_instance.close()
                    logger.info("Central Redis Client закрыт.")

            # 🔥 ИЗМЕНЕНО: Закрываем AsyncIOMotorClient
            if AsyncIOMotorClient in _async_singletons_instances:
                mongo_client_instance = _async_singletons_instances[AsyncIOMotorClient]
                if hasattr(mongo_client_instance, 'close') and callable(mongo_client_instance.close):
                    mongo_client_instance.close() # Motor client.close() - синхронный метод
                    logger.info("MongoDB Client закрыт.")
            
            if engine:
                await engine.dispose()
                logger.info("PostgreSQL Engine закрыт.")
            
    except Exception as e:
        logger.error(f"Ошибка при завершении работы DI-контейнера: {e}", exc_info=True)
    finally:
        inject.clear()
        _async_singletons_instances.clear()
        logger.info("✅ DI-контейнер корректно завершил работу.")