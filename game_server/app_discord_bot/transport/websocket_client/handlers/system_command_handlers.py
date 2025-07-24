# game_server/app_discord_bot/transport/websocket_client/handlers/event_handlers.py

import inject
import logging
from discord.ext import commands

from game_server.contracts.shared_models.websocket_base_models import WebSocketEventPayload


class WSEventHandlers:
    """
    ЗАГЛУШКА: Обработчик событий WebSocket.
    На данный момент просто логирует все входящие события.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} (заглушка) инициализирован.")

    async def handle_event(self, event_data: WebSocketEventPayload):
        """
        Основной метод, который получает все события.
        """
        event_type = event_data.type
        payload = event_data.payload
        
        self.logger.info(f"Получено WebSocket событие '{event_type}'. Payload: {payload}")

        # TODO: Добавить здесь в будущем логику маршрутизации на основе event_type
        # для вызова конкретных обработчиков из слоя системной логики.
        
        # Пока просто логируем, что событие получено и обработано как неизвестное.
        await self.handle_unknown_event(event_data)


    async def handle_unknown_event(self, event_data: WebSocketEventPayload):
        """
        Вызывается для любого события, так как специфичные обработчики еще не реализованы.
        """
        self.logger.debug(f"Событие '{event_data.type}' получено, но специфичный обработчик не реализован.")