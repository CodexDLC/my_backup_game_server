# main.py
import sys
import asyncio
import os
from typing import Optional
from discord.ext import commands
import discord
from dotenv import load_dotenv

# 🔥 ИЗМЕНЕНИЕ: Добавляем импорт нового инициализатора
from game_server.app_discord_bot.app.startup.utils_initializer import UtilsInitializer
# Существующие импорты
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache, BotCacheInitializer
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.app.startup.event_manager import load_events
from game_server.app_discord_bot.config.discord_settings import (
    API_URL, BOT_NAME_FOR_GATEWAY, BOT_PREFIX, DISCORD_TOKEN,
    GAME_SERVER_API, GATEWAY_URL,
    REDIS_BOT_LOCAL_URL, REDIS_BOT_LOCAL_PASSWORD, REDIS_BOT_LOCAL_POOL_SIZE
)
from game_server.app_discord_bot.transport.http_client.http_manager import HTTPManager, create_http_manager
from game_server.app_discord_bot.app.startup.cog_manager import CommandsManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.config.logging.logging_setup import app_logger as logger
# 🔥 ИЗМЕНЕНИЕ: Добавляем импорт для тайп-хинтинга
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager


# 1. Загрузка окружения
load_dotenv()

redis_client_instance: Optional[DiscordRedisClient] = None
bot_cache_instance: Optional[BotCache] = None
pending_requests_orchestrator: Optional[PendingRequestsManager] = None


class GameBot(commands.Bot):
    http_manager: Optional[HTTPManager]
    ws_manager: Optional[WebSocketManager]
    request_helper: Optional[RequestHelper]
    pending_requests_transport_manager: Optional[PendingRequestsManager]
    cache_manager: Optional[BotCache]
    # 🔥 ИЗМЕНЕНИЕ: Добавляем тайп-хинт для нового менеджера
    sync_manager: Optional[CacheSyncManager]

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        logger.info(f"Бот инициализирован с префиксом: {BOT_PREFIX}")

    async def setup_hook(self):
        global redis_client_instance
        global bot_cache_instance
        global pending_requests_orchestrator 

        logger.info("--- Запуск setup_hook ---")

        # 1. Инициализация Redis Client
        logger.info("Инициализация Redis клиента...")
        redis_client_instance = DiscordRedisClient(
            redis_url=REDIS_BOT_LOCAL_URL,
            max_connections=REDIS_BOT_LOCAL_POOL_SIZE,
            redis_password=REDIS_BOT_LOCAL_PASSWORD
        )
        logger.info("✅ Redis клиент создан.")

        # 2. Инициализация всех менеджеров кеша
        logger.info("Инициализация менеджеров кеша...")
        cache_initializer = BotCacheInitializer()
        bot_cache_instance = cache_initializer.initialize(redis_client_instance)
        self.cache_manager = bot_cache_instance
        logger.info("✅ Все менеджеры кеша Redis успешно инициализированы.")

        # 3. Инициализация PendingRequestsManager (оркестратора)
        logger.info("Инициализация PendingRequestsManager (оркестратора)...")
        pending_requests_orchestrator = PendingRequestsManager(
            redis_pending_request_manager=self.cache_manager.pending_requests
        )
        self.pending_requests_transport_manager = pending_requests_orchestrator
        logger.info("✅ PendingRequestsManager (оркестратор) инициализирован.")

        # 4. Инициализация HTTP менеджера
        logger.info("Инициализация HTTP менеджера...")
        self.http_manager = await create_http_manager(base_url=GAME_SERVER_API) 
        logger.info("✅ HTTP менеджер успешно инициализирован.")
        
        # 🔥 ИЗМЕНЕНИЕ: Вместо прямой инициализации RequestHelper вызываем UtilsInitializer
        # 5. Инициализация вспомогательных утилит (RequestHelper, CacheSyncManager)
        logger.info("Инициализация вспомогательных утилит...")
        utils_initializer = UtilsInitializer()
        utils_initializer.initialize(self) # 'self' здесь - это и есть объект bot
        logger.info("✅ Вспомогательные утилиты (RequestHelper, SyncManager) успешно инициализированы.")
        
        # 6. Инициализация WebSocket менеджера
        logger.info("Инициализация WebSocket менеджера...")
        self.ws_manager = WebSocketManager(
            bot=self,
            pending_requests_manager=self.pending_requests_transport_manager,
            bot_name=BOT_NAME_FOR_GATEWAY,
            bot_cache=self.cache_manager
        )
        logger.info("✅ WebSocket менеджер создан.")
        
        # 7. Загрузка событий
        logger.info("Загрузка событий Discord...")
        await load_events(self)
        logger.info("✅ Загрузка событий завершена.")

        # 8. Загрузка когов
        logger.info("Загрузка когов...")
        cog_manager = CommandsManager(self)
        await cog_manager.load_cogs()
        logger.info("✅ Загрузка когов завершена.")

        logger.info("--- setup_hook завершен ---")

    async def on_ready(self):
        """
        Вызывается, когда бот полностью готов и подключен к Discord.
        Теперь self.user доступен.
        """
        logger.info(f"Вошел как {self.user.name} (ID: {self.user.id})")

        logger.info("--- on_ready: ЗАПУСК WS MANAGER ---")
        
        if self.ws_manager:
            logger.debug("Вызов ws_manager.start()...") # Изменено на DEBUG
            self.ws_manager.start()
            logger.info("✅ WebSocket менеджер запущен в фоновом режиме.") # Остается INFO
        else:
            logger.critical("❌ WebSocketManager не был инициализирован в setup_hook!")
            
        logger.debug("--- on_ready: БЛОК ЗАПУСКА WS MANAGER ЗАВЕРШЕН ---") # Изменено на DEBUG
            
            
    async def close(self):
        global redis_client_instance
        global pending_requests_orchestrator 

        logger.info("Начало процесса корректного завершения работы...")
        
        # 1. Останавливаем WebSocket менеджер
        if self.ws_manager:
            await self.ws_manager.disconnect()
            logger.info("🔗 WebSocket менеджер остановлен.")
        
        # 2. Закрываем HTTP сессию
        if self.http_manager:
            if hasattr(self.http_manager, 'session') and not self.http_manager.session.closed:
                await self.http_manager.session.close()
                logger.info("🔗 HTTP сессия закрыта.")
        
        # 3. Закрываем соединение Redis (и завершаем работу менеджеров кеша)
        if redis_client_instance:
            await redis_client_instance.close()
            logger.info("🔗 Redis клиент закрыт. Менеджеры кеша завершили работу.")
        
        # Очищаем pending requests, которые могли остаться висеть
        if pending_requests_orchestrator:
            await pending_requests_orchestrator.shutdown()
            logger.info("Ожидающие запросы очищены из памяти и менеджер завершил работу.")

        await super().close()
        logger.info("🔚 Работа бота завершена.")


async def main():
    bot = GameBot()
    try:
        logger.info("🚀 Запуск бота...")
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.critical("🔑 Неверный токен Discord! Проверьте переменную DISCORD_TOKEN.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске бота: {e}", exc_info=True)
        sys.exit(1)
    finally:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"💥 Непредвиденная ошибка в основном блоке запуска: {e}", exc_info=True)
        sys.exit(1)
