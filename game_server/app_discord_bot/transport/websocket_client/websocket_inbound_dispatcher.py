# game_server/app_discord_bot/transport/websocket_client/websocket_inbound_dispatcher.py

import json
import logging
from typing import Any, Dict

from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage
# Для Prometheus: Определения метрик (примеры)
# from prometheus_client import Counter # <--- Не забудьте установить prometheus_client

# Импортируем контракты


# Импортируем типы обработчиков, чтобы диспетчер мог их использовать
from .handlers.event_handlers import WSEventHandlers # Относительный импорт

# Предполагаем, что PendingRequestsManager также будет доступен и его тип
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager


class WebSocketInboundDispatcher:
    """
    Диспетчер для обработки и маршрутизации входящих текстовых сообщений WebSocket.
    """
    def __init__(
        self,
        logger: logging.Logger,
        pending_requests_manager: PendingRequestsManager,
        event_handler: WSEventHandlers

    ):
        self.logger = logger
        self.pending_requests = pending_requests_manager
        self.event_handler = event_handler
   
        self.logger.debug("DEBUG: WebSocketInboundDispatcher инициализирован.")

    async def dispatch_message(self, text_data: str):
        """
        Обрабатывает и диспетчеризирует входящее текстовое сообщение WebSocket.
        """
        self.logger.debug(f"DEBUG: Диспетчер обрабатывает входящее текстовое сообщение. Длина: {len(text_data)}")
        try:
            data = json.loads(text_data)
            self.logger.debug(f"DEBUG: JSON полученного сообщения: {data}")
            message = WebSocketMessage.model_validate(data) #
            self.logger.debug(f"DEBUG: Валидированное WebSocketMessage. Тип: {message.type}, CorrID: {message.correlation_id}")
            # WS_INBOUND_MESSAGES_PROCESSED.labels(type=message.type).inc() # Prometheus

            if message.type == "RESPONSE": #
                self.logger.debug(f"DEBUG: Сообщение типа RESPONSE, CorrID: {message.correlation_id}")
                

                await self.pending_requests.resolve_request(message.correlation_id, message.model_dump())
                
            elif message.type == "EVENT": #
                self.logger.debug(f"DEBUG: Сообщение типа EVENT, CorrID: {message.correlation_id}")
                # Здесь можно добавить более строгую валидацию payload, если необходимо, используя WebSocketEventPayload
                await self.event_handler.handle_event(message.payload)
            elif message.type == "SYSTEM_COMMAND": #
                self.logger.debug(f"DEBUG: Сообщение типа SYSTEM_COMMAND, CorrID: {message.correlation_id}")
            elif message.type == "AUTH_CONFIRM": #
                self.logger.warning(f"WSManager: AUTH_CONFIRM получен в диспетчере, хотя должен был быть обработан в цикле аутентификации. CorrID: {message.correlation_id}")
            else:
                self.logger.warning(f"WSManager: Неизвестный тип WebSocket сообщения: {message.type}. CorrID: {message.correlation_id}")
        except json.JSONDecodeError:
            self.logger.warning(f"WSManager: Получено не-JSON сообщение: {text_data}")
            # WS_INBOUND_PROCESSING_ERRORS.labels(error_type='json_decode_error').inc() # Prometheus
        except Exception as e:
            self.logger.error(f"WSManager: Ошибка при обработке сообщения: {e}. Данные: {text_data}", exc_info=True)
            # WS_INBOUND_PROCESSING_ERRORS.labels(error_type='general_processing_error').inc() # Prometheus