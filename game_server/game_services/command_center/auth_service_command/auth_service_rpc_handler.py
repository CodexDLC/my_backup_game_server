# game_server/game_services/command_center/auth_service_command/auth_service_rpc_handler.py

import msgpack
from typing import Any, Dict
from aio_pika import IncomingMessage, Message

# Импорты из вашего проекта
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator


class AuthServiceRpcHandler:
    """
    Обрабатывает RPC-запросы для сервиса аутентификации,
    например, для валидации сессионных токенов игроков.
    """
    def __init__(self, message_bus: RabbitMQMessageBus, orchestrator: AuthOrchestrator):
        """
        :param message_bus: Экземпляр шины сообщений.
        :param orchestrator: Экземпляр AuthOrchestrator'а, который умеет проверять токены.
        """
        self._message_bus = message_bus
        self._orchestrator = orchestrator
        self.queue_name = Queues.AUTH_VALIDATE_TOKEN_RPC
        self.logger = logger # <-- ДОБАВЛЕНО: Инициализация логгера
        logger.info(f"✅ AuthServiceRpcHandler инициализирован для очереди '{self.queue_name}'.")

    async def start_listening(self):
        """Начинает прослушивание RPC-очереди."""
        self.logger.info(f"Начинаем прослушивание RPC-запросов в очереди '{self.queue_name}'...")
        # Убедимся, что очередь существует, хотя топология должна ее создавать
        await self._message_bus.declare_queue(self.queue_name)
        # Устанавливаем prefetch_count=1, чтобы один воркер брал только одно сообщение за раз
        await self._message_bus.channel.set_qos(prefetch_count=1)
        await self._message_bus.consume(self.queue_name, self._on_request)
        self.logger.info(f"✅ Слушатель RPC для '{self.queue_name}' успешно запущен.")

    async def _on_request(self, message: IncomingMessage):
        """Обрабатывает входящий RPC-запрос."""
        response_body = {}
        try:
            # Десериализуем тело запроса из MsgPack
            request_data: Dict[str, Any] = msgpack.unpackb(message.body, raw=False)

            self.logger.info(f"Получен RPC-запрос на валидацию токена для игрока {request_data.get('player_id', 'N/A')}.")

            # Вызываем логику проверки токена из оркестратора
            # Передаем ВЕСЬ СЛОВАРЬ request_data
            validation_result = await self._orchestrator.validate_session_token(request_data) 
            
            response_body = validation_result

        except Exception as e:
            self.logger.error(f"Ошибка при обработке RPC-запроса (correlation_id: {message.correlation_id}): {e}", exc_info=True)
            response_body = {"is_valid": False, "error": str(e)}
            
        finally:
            # Публикуем ответ, если есть обратный адрес
            if message.reply_to:
                await self._message_bus.channel.default_exchange.publish(
                    Message(
                        body=msgpack.dumps(response_body, use_bin_type=True),
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to
                )
            
            # Подтверждаем получение и обработку исходного сообщения
            await message.ack()
