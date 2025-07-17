# game_server/Logic/InfrastructureLogic/app_cache/app_cache_initializer.py

import logging
from typing import Optional, Dict, Any, Type

# Импортируем CentralRedisClient
from .central_redis_client import CentralRedisClient

# Импортируем настройки Redis
from game_server.config.settings_core import REDIS_URL, REDIS_POOL_SIZE, REDIS_PASSWORD
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 УДАЛЕНО: Импорт _async_singletons_instances из di_container
# from game_server.core.di_container import _async_singletons_instances


async def initialize_app_cache_managers() -> Optional[CentralRedisClient]: # 🔥 ИЗМЕНЕНИЕ: Теперь возвращает CentralRedisClient
    """
    Инициализирует CentralRedisClient.
    """
    logger.info("🔧 Инициализация CentralRedisClient для кэш-менеджеров...")

    central_redis_client_instance = None # Инициализируем None для обработки ошибок
    try:
        # 1. Инициализация CentralRedisClient
        central_redis_client_instance = CentralRedisClient(
            redis_url=REDIS_URL,
            max_connections=REDIS_POOL_SIZE,
            redis_password=REDIS_PASSWORD
        )
        await central_redis_client_instance.connect()
        logger.info("✅ CentralRedisClient успешно инициализирован.")
        
        # DEBUG-проверка (оставляем, если нужна)
        if not hasattr(central_redis_client_instance, 'hgetall_msgpack'):
            logger.critical("DEBUG: !!! CENTRAL_REDIS_CLIENT НЕ ИМЕЕТ hgetall_msgpack ПРИ ИНИЦИАЛИЗАЦИИ CACHE MANAGERS !!!")
            raise AttributeError(f"DEBUG: Global CentralRedisClient from module '{central_redis_client_instance.__class__.__module__}' has no attribute 'hgetall_msgpack'")
        logger.critical("--- DEBUG: CentralRedisClient Проверка завершена ---")

        logger.info("✅ Инициализация CentralRedisClient для кэш-менеджеров завершена.")
        return central_redis_client_instance # 🔥 ИЗМЕНЕНИЕ: Возвращаем экземпляр
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации CentralRedisClient: {e}", exc_info=True)
        if central_redis_client_instance:
            await central_redis_client_instance.close()
            logger.warning("CentralRedisClient закрыт после ошибки инициализации менеджеров.")
        return None # 🔥 ИЗМЕНЕНИЕ: Возвращаем None при ошибке


async def shutdown_app_cache_managers() -> None:
    """
    Завершает работу CentralRedisClient.
    """
    logger.info("🛑 Завершение работы CentralRedisClient...")
    # 🔥 ИЗМЕНЕНИЕ: Теперь нужно будет получить CentralRedisClient из inject.instance()
    # или передать его сюда, если он не управляется inject'ом для завершения.
    # Для избежания циклического импорта, эта функция не должна получать его из _async_singletons_instances.
    # Вместо этого, логика закрытия будет в di_container.py, который получит его через inject.instance().
    # Здесь можно оставить заглушку или логику, которая не требует доступа к _async_singletons_instances.
    logger.info("✅ CentralRedisClient завершение работы (логика в di_container).")

