import asyncio
import json
import logging
import aio_pika
from typing import Optional, Dict, Any

# Импортируем только RABBITMQ_URL
from game_server.settings import RABBITMQ_URL #

logger = logging.getLogger(__name__)

class RabbitMQClient:
    """
    Центральный клиент для взаимодействия с RabbitMQ.
    Управляет соединением, каналами и публикацией сообщений.
    """
    def __init__(self):
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._is_connected = False
        logger.info("✅ RabbitMQClient инициализирован.")

    async def connect(self):
        """Устанавливает устойчивое соединение с RabbitMQ."""
        if self._is_connected and self._connection and not self._connection.is_closed:
            logger.info("RabbitMQClient: Уже подключен.")
            return

        try:
            self._connection = await aio_pika.connect_robust(
                url=RABBITMQ_URL,
                loop=asyncio.get_running_loop()
            )
            self._channel = await self._connection.channel()
            self._is_connected = True
            # 🔥 ИСПРАВЛЕНИЕ: Логируем только хост/порт или замаскированный URL 🔥
            # Извлекаем хост и порт из URL для безопасного логирования
            parsed_url = aio_pika.connection.URL(RABBITMQ_URL)
            safe_url = f"amqp://{parsed_url.host}:{parsed_url.port}/" #
            logger.info(f"✅ RabbitMQClient успешно подключен к {safe_url}") #
        except Exception as e:
            self._is_connected = False
            logger.critical(f"❌ Ошибка подключения к RabbitMQ: {str(e)}", exc_info=True)
            raise ConnectionError(f"Ошибка подключения к RabbitMQ: {str(e)}")

    async def close(self):
        """Закрывает соединение с RabbitMQ."""
        if self._channel:
            await self._channel.close()
            self._channel = None
        if self._connection:
            await self._connection.close()
            self._connection = None
        self._is_connected = False
        logger.info("👋 RabbitMQClient: Соединение закрыто.")

    async def publish_message(
        self,
        queue_name: str,
        message_body: Dict[str, Any],
        delivery_mode: aio_pika.DeliveryMode = aio_pika.DeliveryMode.PERSISTENT,
        exchange_name: str = ''
    ):
        """
        Публикует сообщение в указанную очередь RabbitMQ.
        """
        if not self._is_connected or not self._channel:
            logger.error("❌ RabbitMQClient не подключен. Не могу отправить сообщение.")
            return

        try:
            message_json = json.dumps(message_body).encode('utf-8')
            message = aio_pika.Message(
                body=message_json,
                content_type='application/json',
                delivery_mode=delivery_mode
            )
            
            exchange = self._channel.default_exchange if not exchange_name else await self._channel.get_exchange(exchange_name)

            await exchange.publish(
                message,
                routing_key=queue_name
            )
            logger.debug(f"✅ RabbitMQClient: Сообщение отправлено в очередь '{queue_name}'.")
        except Exception as e:
            logger.error(f"❌ RabbitMQClient: Ошибка при публикации сообщения в очередь '{queue_name}': {e}", exc_info=True)


# Создаем единственный экземпляр клиента для всего приложения
rabbitmq_client = RabbitMQClient()