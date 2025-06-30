# game_server/game_services/command_center/auth_service_command/auth_issue_token_rpc_handler.py

import msgpack
from typing import Any, Dict
from aio_pika import IncomingMessage, Message

# Импорты из вашего проекта
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator


class AuthIssueTokenRpcHandler:
    """
    Обрабатывает RPC-запросы для сервиса аутентификации,
    касающиеся выдачи новых токенов (например, для ботов или игроков).
    """
    def __init__(self, message_bus: RabbitMQMessageBus, orchestrator: AuthOrchestrator):
        self._message_bus = message_bus
        self._orchestrator = orchestrator
        self.queue_name = Queues.AUTH_ISSUE_BOT_TOKEN_RPC # Эта очередь для выдачи токенов ботам
        logger.info(f"✅ AuthIssueTokenRpcHandler инициализирован для очереди '{self.queue_name}'.")

    async def start_listening(self):
        """Начинает прослушивание RPC-очереди для выдачи токенов."""
        logger.info(f"Начинаем прослушивание RPC-запросов в очереди '{self.queue_name}'...")
        await self._message_bus.declare_queue(self.queue_name)
        await self._message_bus.channel.set_qos(prefetch_count=1)
        await self._message_bus.consume(self.queue_name, self._on_request)
        logger.info(f"✅ Слушатель RPC для '{self.queue_name}' (выдача токенов) успешно запущен.")

    async def _on_request(self, message: IncomingMessage):
        """Обрабатывает входящий RPC-запрос на выдачу токена."""
        response_body = {}
        try:
            # ВОЗВРАЩАЕМ: Десериализуем тело запроса из MsgPack
            request_data: Dict[str, Any] = msgpack.unpackb(message.body, raw=False) # <--- ЭТУ СТРОКУ НУЖНО ВЕРНУТЬ
            
            # ЭТО ВАЖНО: Вызываем новый метод оркестратора для выдачи токена
            issue_result = await self._orchestrator.issue_auth_token(request_data) 
            
            response_body = issue_result

        except Exception as e:
            logger.error(f"Ошибка при обработке RPC-запроса на выдачу токена (correlation_id: {message.correlation_id}): {e}", exc_info=True)
            response_body = {"success": False, "error": str(e)}



        finally:
            if message.reply_to:
                await self._message_bus.channel.default_exchange.publish(
                    Message(
                        body=msgpack.dumps(response_body, use_bin_type=True),
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to
                )
            await message.ack()