# game_server/app_gateway/gateway/event_broadcast_handler.py

import asyncio
import msgpack
import uuid # ✅ НУЖЕН для correlation_id
from typing import Optional

from aio_pika import IncomingMessage

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.gateway.client_connection_manager import ClientConnectionManager
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
# ✅ Импортируем обе необходимые модели
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketEventPayload


class EventBroadcastHandler:
    """
    Обработчик, который получает события от бэкенда и рассылает их
    ВСЕМ активным WebSocket-клиентам.
    """
    # ... (__init__ и start_listening_for_events без изменений) ...
    def __init__(
        self,
        message_bus: IMessageBus,
        client_connection_manager: ClientConnectionManager
    ):
        self.message_bus = message_bus
        self.client_connection_manager = client_connection_manager
        self.logger = logger
        self._listen_task: Optional[asyncio.Task] = None
        self.inbound_queue_name = Queues.GATEWAY_INBOUND_EVENTS
        self.logger.info("✅ EventBroadcastHandler (режим broadcast-to-all) инициализирован.")

    async def start_listening_for_events(self):
        """Запускает прослушивание очереди входящих событий."""
        if self._listen_task is None or self._listen_task.done():
            self.logger.info(f"🎧 Начинаю слушать события из очереди '{self.inbound_queue_name}' для массовой рассылки.")
            self._listen_task = asyncio.create_task(self._listen_loop())
        else:
            self.logger.warning("EventBroadcastHandler уже запущен.")

    async def _listen_loop(self):
        """Основной цикл, который передает колбэк в message_bus."""
        try:
            await self.message_bus.consume(self.inbound_queue_name, self._on_message_received)
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при запуске EventBroadcastHandler: {e}", exc_info=True)
            raise

    async def _on_message_received(self, message: IncomingMessage):
        """
        Колбэк, вызываемый при получении события из RabbitMQ.
        Правильно упаковывает событие и пересылает его всем.
        """
        try:
            async with message.process():
                # --- ✅ ПРАВИЛЬНАЯ ОБРАБОТКА СООБЩЕНИЯ ---
                self.logger.info("EventBroadcastHandler: Обработка входящего сообщения...")
                event_data = msgpack.unpackb(message.body, raw=False)
                routing_key = message.routing_key or "event.unknown"
                self.logger.info(f"Получено событие '{routing_key}'")
                self.logger.debug(f"Для рассылки всем: {event_data}")
                
                all_client_ids = list(self.client_connection_manager.active_connections.keys())
                if not all_client_ids:
                    return

                # --- ✅ ПРАВИЛЬНАЯ УПАКОВКА СООБЩЕНИЯ ---
                
                # 1. Создаем "внутренний" payload события
                event_payload = WebSocketEventPayload(
                    type=routing_key,  # Тип события, например "event.location.updated"
                    payload=event_data # Данные события, например {"location_id": "201"}
                )
                self.logger.debug(f"Создан WebSocketEventPayload: {event_payload.model_dump()}")

                # 2. Создаем "внешний конверт" WebSocketMessage
                websocket_msg = WebSocketMessage(
                    type="EVENT", # Тип "конверта" - 'EVENT' в верхнем регистре
                    correlation_id=uuid.uuid4(), # Генерируем новый UUID для этого сообщения
                    payload=event_payload # Вкладываем наш payload события
                )
                message_json = websocket_msg.model_dump_json()

                # Рассылаем всем
                self.logger.info(f"Рассылка события '{routing_key}' {len(all_client_ids)} клиентам.")
                for client_id in all_client_ids:
                    await self.client_connection_manager.send_message_to_client(client_id, message_json)

        except Exception as e:
            self.logger.error(f"Ошибка при массовой рассылке события: {e}", exc_info=True)