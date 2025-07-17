# game_server/app_discord_bot/core/di_container.py

import aiohttp
import discord
import inject
import logging
from typing import Dict, Any, Type, Optional

# Импорты всех модулей привязок для бота
from game_server.app_discord_bot.app.services.utils.name_formatter import NameFormatter
from game_server.app_discord_bot.core.di_modules.bot_cache_bindings import configure_bot_cache
from game_server.app_discord_bot.core.di_modules.bot_orchestrator_bindings import configure_bot_orchestrators
from game_server.app_discord_bot.core.di_modules.bot_transport_bindings import configure_bot_transport
from game_server.app_discord_bot.core.di_modules.bot_service_bindings import configure_bot_services

from game_server.app_discord_bot.config import discord_settings
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.transport.http_client.http_manager import HTTPManager, create_http_manager
from game_server.config.logging.logging_setup import app_logger as global_app_logger

logger = logging.getLogger(__name__)

_async_singletons_instances: Dict[Type | str, Any] = {}

def configure_bot_dependencies(binder, bot_instance: Any):
    """
    Конфигурирует все зависимости Discord-бота.
    """
    logger.info("🔧 Конфигурирование DI-контейнера Discord-бота...")
    
    binder.bind(logging.Logger, global_app_logger)

    from game_server.app_discord_bot.main import GameBot
    from discord.ext import commands

    binder.bind(GameBot, bot_instance)
    binder.bind(commands.Bot, bot_instance)
    binder.bind(discord.Client, bot_instance)
    
    
    
    # Привязка асинхронных синглтонов, которые уже инициализированы
    for singleton_class, instance in _async_singletons_instances.items():
        binder.bind(singleton_class, instance)
     
    # Вызываем дочерние конфигураторы, передавая bot_instance там, где это необходимо
    configure_bot_cache(binder)
    configure_bot_transport(binder, bot_instance)
    configure_bot_services(binder, bot_instance)
    configure_bot_orchestrators(binder)
    
    logger.info("✅ DI-контейнер Discord-бота сконфигурирован.")

    
async def initialize_bot_di_container(bot_instance: Any):
    """
    Инициализирует DI-контейнер и все основные асинхронные синглтоны.
    """
    logger.info("🔧 Инициализация DI-контейнера Discord-бота...")
    
    # 1. Инициализация DiscordRedisClient
    redis_client = DiscordRedisClient(
        redis_url=discord_settings.REDIS_BOT_LOCAL_URL,
        max_connections=discord_settings.REDIS_BOT_LOCAL_POOL_SIZE,
        redis_password=discord_settings.REDIS_BOT_LOCAL_PASSWORD
    )
    _async_singletons_instances[DiscordRedisClient] = redis_client
    logger.info("✅ DiscordRedisClient успешно инициализирован.")

    # 2. Инициализация HTTPManager
    logger.info("Инициализация HTTPManager...")
    session = aiohttp.ClientSession(
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    http_manager = await create_http_manager(
        session, 
        discord_settings.GAME_SERVER_API, 
        discord_settings.BOT_NAME_FOR_GATEWAY
    )
    setattr(http_manager, '_session_to_close', session)
    _async_singletons_instances[HTTPManager] = http_manager
    logger.info("✅ HTTPManager успешно инициализирован.")
    
    # 3. Инициализация NameFormatter
    from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
    name_formatter = NameFormatter(
        logger=global_app_logger,
        emojis_formatting_config=CHANNELS_CONFIG["emojis_formatting"]
    )
    _async_singletons_instances[NameFormatter] = name_formatter
    logger.info("✅ NameFormatter успешно инициализирован.")

    # Финальная конфигурация inject
    inject.clear_and_configure(lambda binder: configure_bot_dependencies(binder, bot_instance))
    
    logger.info("✅ DI-контейнер Discord-бота успешно сконфигурирован.")
    logger.info("--- Все асинхронные синглтоны Discord-бота инициализированы. ---")

    
async def shutdown_bot_di_container():
    """
    Корректно завершает работу всех асинхронных зависимостей.
    """
    logger.info("🛑 Завершение работы DI-контейнера Discord-бота...")
    try:
        redis_client_instance = _async_singletons_instances.get(DiscordRedisClient)
        if redis_client_instance:
            await redis_client_instance.close()
            logger.info("🔗 DiscordRedisClient закрыт.")

        http_manager_instance = _async_singletons_instances.get(HTTPManager)
        if http_manager_instance and hasattr(http_manager_instance, '_session_to_close') and not http_manager_instance._session_to_close.closed:
            await http_manager_instance._session_to_close.close()
            logger.info("🔗 HTTPManager сессия закрыта.")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении работы DI-контейнера: {e}", exc_info=True)
    finally:
        inject.clear()
        _async_singletons_instances.clear()
        logger.info("✅ DI-контейнер Discord-бота корректно завершил работу.")
