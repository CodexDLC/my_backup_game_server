# transport/websocket_client/event_handlers.py
from game_server.common_contracts.shared_models.api_contracts import WebSocketEventPayload
from game_server.config.logging.logging_setup import app_logger as logger


class WSEventHandlers:
    """
    Диспетчер для обработки асинхронных событий, полученных от сервера.
    """
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_event(self, event_data: WebSocketEventPayload):
        """
        Главный метод, который вызывает нужный обработчик в зависимости от типа события.
        """
        event_type = event_data.type
        # Преобразуем 'PLAYER_MOVED' в 'handle_player_moved_event'
        handler_name = f"handle_{event_type.lower()}_event"
        handler_method = getattr(self, handler_name, self.handle_unknown_event)
        
        logger.info(f"Получено WebSocket событие '{event_type}'. Вызов '{handler_name}'...")
        await handler_method(event_data)

    async def handle_unknown_event(self, event_data: WebSocketEventPayload):
        logger.warning(f"Получено неизвестное событие типа '{event_data.type}'.")

    # Здесь будут конкретные обработчики
    # async def handle_player_moved_event(self, event_data: WebSocketEventPayload):
    #     logger.info(f"Обработано событие перемещения игрока: {event_data.payload}")

