# game_server/app_discord_bot/main.py
import sys
import asyncio

from typing import Optional
from discord.ext import commands
import discord
from dotenv import load_dotenv

# 🔥 ИЗМЕНЕНИЕ: Импортируем функции инициализации/остановки DI-контейнера бота

from game_server.app_discord_bot.core.di_container import initialize_bot_di_container, shutdown_bot_di_container

# Импорты для загрузки когов и событий
from game_server.app_discord_bot.app.startup.event_manager import EventManager
from game_server.app_discord_bot.app.startup.cog_manager import CommandsManager # Этот менеджер будет загружать наш Cog

# Импорты настроек бота
from game_server.app_discord_bot.config.discord_settings import (
    BOT_PREFIX, DISCORD_TOKEN,
)

# Импорты классов, которые будут инжектироваться в GameBot для доступа в setup_hook
# 🔥 ВАЖНО: Эти импорты нужны только для типизации и для явного запроса inject.instance()
# в setup_hook. Сами классы будут привязаны в di_modules.
from game_server.app_discord_bot.app.startup.ui_initializer.ui_initializer import UIInitializer
from game_server.app_discord_bot.transport.http_client.http_manager import HTTPManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager


from game_server.config.logging.logging_setup import app_logger as logger
import inject # 🔥 ДОБАВЛЕНО: Импортируем inject


class GameBot(commands.Bot):
    # Объявляем типы для полей, которые будут инициализированы через DI
    http_manager: Optional[HTTPManager]
    ws_manager: Optional[WebSocketManager]
    request_helper: Optional[RequestHelper]
    pending_requests_transport_manager: Optional[PendingRequestsManager]
    cache_manager: Optional[BotCache]
    sync_manager: Optional[CacheSyncManager]
    ui_initializer: Optional[UIInitializer] # 🔥 НОВОЕ: Добавляем тип для UIInitializer

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # Для доступа к информации о пользователях сервера
        intents.message_content = True  # Для чтения содержимого текстовых сообщений
        intents.guilds = True           # Для получения информации о гильдиях (серверах)
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        logger.info(f"Бот инициализирован с префиксом: {BOT_PREFIX}")

    async def setup_hook(self):
        """
        setup_hook вызывается после логина бота, но до on_ready.
        Идеальное место для инициализации DI-контейнера и получения основных сервисов.
        """
        logger.info("--- Запуск setup_hook ---")
        
        # Инициализация DI-контейнера, передаем экземпляр бота (self) для привязки
        # Это должно произойти до любого inject.instance(), чтобы зависимости были доступны
        await initialize_bot_di_container(self)
        logger.debug("DI-контейнер инициализирован.")

        # Получаем все основные менеджеры и сервисы через inject
        self.http_manager = inject.instance(HTTPManager)
        self.pending_requests_transport_manager = inject.instance(PendingRequestsManager)
        self.cache_manager = inject.instance(BotCache)
        self.request_helper = inject.instance(RequestHelper)
        self.sync_manager = inject.instance(CacheSyncManager)
        self.ws_manager = inject.instance(WebSocketManager) 
        self.ui_initializer = inject.instance(UIInitializer) # 🔥 НОВОЕ: Получаем UIInitializer

        logger.info("✅ Все основные менеджеры и сервисы успешно инициализированы через DI.")
        
        # Загрузка обработчиков событий Discord (через event_manager.py)
        logger.info("Загрузка событий Discord...")
        # 🔥 ИЗМЕНЕНИЕ: Получаем экземпляр EventManager через DI и регистрируем события
        event_manager = inject.instance(EventManager)
        event_manager.register_events()
        logger.info("✅ Загрузка событий завершена.")

        # Загрузка когов (команд) (через cog_manager.py)
        # CommandsManager, как я понял из вашего кода, управляет загрузкой когов.
        # Убедитесь, что CommandsManager способен загружать коги, которые используют inject.autoparams().
        logger.info("Загрузка когов...")
        cog_manager = CommandsManager(self) # Передаем экземпляр бота CommandsManager
        await cog_manager.load_cogs() # Этот метод должен загрузить, в том числе, RegistrationCog
        logger.info("✅ Загрузка когов завершена.")

        logger.info("--- setup_hook завершен ---")
        
    async def on_ready(self):
        """
        Вызывается, когда бот полностью готов и подключен к Discord.
        Здесь self.user доступен.
        """
        logger.info(f"✅ Вошел как {self.user.name} (ID: {self.user.id})") # Теперь этот лог будет первым
            
        logger.info("--- on_ready: ЗАПУСК WS MANAGER ---")
        
        if hasattr(self, 'ws_manager') and self.ws_manager:
            logger.debug("Вызов ws_manager.start()...")
            
            try:
                if asyncio.iscoroutinefunction(self.ws_manager.start):
                    await self.ws_manager.start()
                else:
                    self.ws_manager.start()
                
                logger.info("✅ WebSocket менеджер запущен в фоновом режиме.")
            except Exception as e:
                logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ WS MANAGER В on_ready: {e}", exc_info=True)
                import traceback
                traceback.print_exc()
        else:
            logger.critical("❌ WebSocketManager не был инициализирован в setup_hook!")
            
        logger.debug("--- on_ready: БЛОК ЗАПУСКА WS MANAGER ЗАВЕРШЕН ---")
        
        # 🔥 НОВОЕ: Инициализация постоянных View здесь, после того как бот полностью готов.
        # Это важно, так как bot.add_view() лучше вызывать после полного подключения.
        if self.ui_initializer:
            await self.ui_initializer.initialize_persistent_views()
        else:
            logger.critical("❌ UIInitializer не был инициализирован в setup_hook!")
            
    async def close(self):
        logger.info("Начало процесса корректного завершения работы...")
        
        if self.ws_manager:
            await self.ws_manager.disconnect()
            logger.info("🔗 WebSocket менеджер остановлен.")
        
        await shutdown_bot_di_container()
        logger.info("🔗 Redis клиент и другие асинхронные зависимости закрыты.")
        
        await super().close()
        logger.info("🔚 Работа бота завершена.")


async def main():
    load_dotenv() 
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