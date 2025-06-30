# game_server/app_gateway/gateway/websocket_outbound_dispatcher.py

import asyncio
import json
import msgpack
from typing import Optional, Dict, Any

from aio_pika import IncomingMessage

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.gateway.client_connection_manager import ClientConnectionManager
from game_server.common_contracts.shared_models.api_contracts import WebSocketMessage, WebSocketResponsePayload
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues


class OutboundWebSocketDispatcher:
    """
    Универсальный диспетчер для всех исходящих WebSocket-сообщений.
    Потребляет сообщения из единой очереди RabbitMQ и отправляет их
    в соответствующее активное WebSocket-соединение.
    """
    def __init__(
        self,
        message_bus: IMessageBus,
        client_connection_manager: ClientConnectionManager
    ):
        self.message_bus = message_bus
        self.client_connection_manager = client_connection_manager
        self.logger = logger
        self._listen_task: Optional[asyncio.Task] = None
        self.outbound_queue_name = Queues.GATEWAY_OUTBOUND_WS_MESSAGES
        self.logger.info("✅ OutboundWebSocketDispatcher инициализирован.")

    async def start_listening_for_outbound_messages(self):
        """Запускает прослушивание общей очереди исходящих WebSocket-сообщений."""
        if self._listen_task is None or self._listen_task.done():
            self.logger.info(f"🎧 Начинаю слушать исходящие WS сообщения из очереди '{self.outbound_queue_name}'.")
            self._listen_task = asyncio.create_task(self._listen_loop())
        else:
            self.logger.warning("OutboundWebSocketDispatcher уже запущен.")

    async def _listen_loop(self):
        """Основной цикл, который передает колбэк в message_bus."""
        try:
            await self.message_bus.consume(self.outbound_queue_name, self._on_message_received)
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при запуске OutboundWebSocketDispatcher: {e}", exc_info=True)
            raise

    async def _on_message_received(self, message: IncomingMessage):
        """
        Колбэк, вызываемый при получении сообщения из RabbitMQ.
        Десериализует, находит адресата и отправляет сообщение по WebSocket.
        """
        message_envelope: Optional[Dict[str, Any]] = None
        actual_websocket_message_data: Optional[Dict[str, Any]] = None

        self.logger.info(f"OutboundDispatcher: Получено сырое сообщение. Body length: {len(message.body)}")
        self.logger.debug(f"OutboundDispatcher: Сырое сообщение body (raw bytes): {message.body}")

        try:
            message_envelope = msgpack.unpackb(message.body, raw=False)
            self.logger.info(f"OutboundDispatcher: Сообщение MsgPack распаковано. Тип внешней обертки: {type(message_envelope)}. Содержимое (частично): {str(message_envelope)[:200]}")

            if not isinstance(message_envelope, dict) or 'payload' not in message_envelope:
                self.logger.warning(f"Получено сообщение без ожидаемого поля 'payload' или не словарь. Сообщение: {message.body.decode(errors='ignore')[:200]}...")
                await message.ack()
                return
            
            actual_websocket_message_data = message_envelope['payload']
            self.logger.info(f"OutboundDispatcher: Извлечен фактический WebSocketMessage. Тип: {type(actual_websocket_message_data)}. Содержимое (частично): {str(actual_websocket_message_data)[:200]}")

            websocket_msg = WebSocketMessage.model_validate(actual_websocket_message_data)
            self.logger.info("OutboundDispatcher: Сообщение успешно валидировано как WebSocketMessage.")

            # Получаем client_id напрямую из websocket_msg
            target_client_id = websocket_msg.client_id
            
            if not target_client_id:
                self.logger.warning(f"Сообщение (CorrID: {websocket_msg.correlation_id}) не может быть доставлено: отсутствует 'client_id' на верхнем уровне WebSocketMessage.")
                await message.ack()
                return

            message_json = websocket_msg.model_dump_json()
            self.logger.info(f"OutboundDispatcher: Отправка JSON-сообщения клиенту {target_client_id}...")

            success = await self.client_connection_manager.send_message_to_client(
                target_client_id,
                message_json
            )

            if success:
                self.logger.debug(f"Ответ для клиента {target_client_id} (CorrID: {websocket_msg.correlation_id}) успешно отправлен.")
            else:
                self.logger.warning(f"Не удалось отправить сообщение клиенту {target_client_id}. Соединение не найдено или закрыто.")

            await message.ack()
        except Exception as e:
            msg_id = actual_websocket_message_data.get("correlation_id", "N/A") if actual_websocket_message_data else "N/A"
            self.logger.error(f"Ошибка при обработке исходящего WebSocket-сообщения (CorrID: {msg_id}): {e}", exc_info=True)
            await message.nack(requeue=False)
