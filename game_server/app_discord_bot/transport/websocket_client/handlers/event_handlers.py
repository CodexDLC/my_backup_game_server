# game_server/app_discord_bot/transport/websocket_client/event_handlers.py
import inject
import logging
import discord
from discord.ext import commands

from game_server.contracts.shared_models.websocket_base_models import WebSocketEventPayload

# 🔥 ИЗМЕНЕНИЕ: УДАЛИТЬ ИМПОРТ ГЛОБАЛЬНОГО ЛОГГЕРА
# from game_server.config.logging.logging_setup import app_logger as logger # УДАЛИТЬ ЭТУ СТРОКУ

class WSEventHandlers:
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger = None): # Логгер инжектируется
        self.bot = bot
        self.logger = logger if logger is not None else logging.getLogger(__name__) # Используем инжектированный логгер
    
        self.logger.info("WSEventHandlers: Инициализация.") # 🔥 ДОБАВЛЕНО ДЛЯ ОТЛАДКИ

    async def handle_event(self, event_data: WebSocketEventPayload):
        event_type = event_data.type
        handler_name = f"handle_{event_type.lower()}_event"
        handler_method = getattr(self, handler_name, self.handle_unknown_event)
        
        self.logger.info(f"Получено WebSocket событие '{event_type}'. Вызов '{handler_name}'...")

        try: # 🔥 ДОБАВЛЕНО ДЛЯ ОТЛАДКИ
            await handler_method(event_data)
        except Exception as e:
            self.logger.critical(f"WSEventHandlers: Ошибка в обработчике события '{event_type}': {e}", exc_info=True)


    async def handle_unknown_event(self, event_data: WebSocketEventPayload):
        self.logger.warning(f"Получено неизвестное событие типа '{event_data.type}'.")

    # Здесь будут конкретные обработчики
    # async def handle_player_moved_event(self, event_data: WebSocketEventPayload):
    #     self.logger.info(f"Обработано событие перемещения игрока: {event_data.payload}")