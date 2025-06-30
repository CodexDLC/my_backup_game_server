# game_server/app_discord_bot/app/startup/utils_initializer.py
import discord
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 ИЗМЕНЕНИЕ: Добавляем импорт настроек
from game_server.app_discord_bot.config.discord_settings import BOT_NAME_FOR_GATEWAY

# Импортируем наши классы-утилиты
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager

class UtilsInitializer:
    """
    Инициализирует и "прикрепляет" к объекту бота все вспомогательные
    сервисы и менеджеры (утилиты).
    """
    def initialize(self, bot: discord.Client) -> None:
        """
        Создает экземпляры всех утилит и сохраняет их в bot.
        """
        try:
            # 🔥 ИЗМЕНЕНИЕ: Правильная инициализация RequestHelper
            # Передаем все необходимые зависимости, которые уже есть в bot
            bot.request_helper = RequestHelper(
                pending_requests_manager=bot.pending_requests_transport_manager,
                http_client_gateway=bot.http_manager,
                bot_name=BOT_NAME_FOR_GATEWAY
            )
            
            # Инициализация CacheSyncManager теперь будет работать,
            # так как он найдет bot.request_helper
            bot.sync_manager = CacheSyncManager(bot)
            
            logger.success("✨ Все утилиты (RequestHelper, CacheSyncManager) успешно инициализированы.")
        except Exception as e:
            logger.critical(f"💥 Критическая ошибка при инициализации утилит: {e}", exc_info=True)
            raise