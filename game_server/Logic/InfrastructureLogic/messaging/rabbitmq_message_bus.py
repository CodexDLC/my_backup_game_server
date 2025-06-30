# game_server/Logic/InfrastructureLogic/messaging/rabbitmq_message_bus.py

import asyncio
import uuid
import msgpack
from typing import Dict, Any, Optional, Callable
from asyncio import Future
import aio_pika
from aio_pika import IncomingMessage, Message, ExchangeType
from datetime import datetime # 🔥 НОВЫЙ ИМПОРТ: datetime для кастомного сериализатора

from game_server.config.provider import config # Использует config.settings.core.AMQP_URL
from game_server.config.settings.rabbitmq.rabbitmq_topology import RABBITMQ_TOPOLOGY_SETUP 
from .i_message_bus import IMessageBus
from .message_format import create_message # 🔥 Убедитесь, что create_message правильно форматирует


from game_server.config.logging.logging_setup import app_logger as logger


# 🔥 НОВАЯ ФУНКЦИЯ: Кастомный сериализатор для msgpack
def msgpack_default(obj):
    """
    Функция-сериализатор по умолчанию для msgpack,
    обрабатывающая неподдерживаемые типы данных, такие как UUID и datetime.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj) # Преобразуем UUID в строку
    if isinstance(obj, datetime):
        return obj.isoformat() # Преобразуем datetime в ISO 8601 строку
    raise TypeError(f"Object of type {obj.__class__.__name__} is not MsgPack serializable")


class RabbitMQMessageBus(IMessageBus):
    """
    Реализация шины сообщений для RabbitMQ с поддержкой
    стандартной публикации (Publish/Subscribe) и удаленного вызова процедур (RPC).
    """
    def __init__(self):
        # Используем config.settings.core.AMQP_URL, как это было в вашем файле
        self.amqp_url = config.settings.core.AMQP_URL 
        if not self.amqp_url:
            raise ValueError("AMQP_URL не найден в конфигурации RabbitMQ.")
        
        self.connection = None
        self.channel = None
        self._consumer_tasks = [] 
        
        self._rpc_futures: Dict[str, Future] = {}
        self._rpc_callback_queue: Optional[aio_pika.abc.AbstractQueue] = None

        logger.debug("RabbitMQMessageBus инициализирован.")

    async def connect(self):
        """
        Устанавливает соединение, создает канал и настраивает топологию,
        включая инфраструктуру для RPC.
        """
        if self.connection and not self.connection.is_closed:
            logger.info("Соединение с RabbitMQ уже активно.")
            return

        try:
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()
            logger.info("✅ Успешное подключение к RabbitMQ и создание канала.")
            
            await self._setup_topology()
            
            await self._setup_rpc()

        except Exception as e:
            logger.error(f"❌ Критическая ошибка подключения к RabbitMQ: {e}", exc_info=True)
            raise

    async def _setup_topology(self):
        """
        Создает обменники, очереди и их связи на основе предопределенной топологии.
        Это гарантирует, что RabbitMQ настроен правильно при старте приложения.
        """
        logger.info("Настройка топологии RabbitMQ...")
        for item in RABBITMQ_TOPOLOGY_SETUP: # Использует RABBITMQ_TOPOLOGY_SETUP
            item_type = item["type"]
            try:
                if item_type == "exchange":
                    spec = item["spec"] 
                    await self.channel.declare_exchange(name=spec["name"], type=spec["type"], durable=spec["durable"])
                    logger.debug(f"Объявлен обменник: {spec['name']} ({spec['type']})")
                elif item_type == "queue":
                    spec = item["spec"]
                    arguments = spec.get("arguments") 
                    await self.channel.declare_queue(name=spec["name"], durable=spec["durable"], arguments=arguments)
                    logger.debug(f"Объявлена очередь: {spec['name']}")
                elif item_type == "binding":
                    queue = await self.channel.get_queue(item["destination"])
                    await queue.bind(item["source"], item["routing_key"])
                    logger.debug(f"Создана связь: {item['source']} -> {item['destination']} (ключ: {item['routing_key']})")
                else:
                    logger.warning(f"Неизвестный тип элемента топологии: {item_type}")
            except Exception as e:
                item_name = item.get("spec", {}).get("name", item.get("destination", "UNKNOWN"))
                logger.error(f"Ошибка при настройке элемента топологии {item_type} '{item_name}': {e}", exc_info=True)
        logger.info("✅ Топология RabbitMQ успешно настроена.")

    async def publish(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """
        Публикует сообщение в указанный обменник с заданным ключом маршрутизации.
        Сообщение форматируется и сериализуется в MsgPack.
        """
        if not self.channel or self.channel.is_closed:
            raise ConnectionError("Канал RabbitMQ не активен или закрыт. Вызовите connect() перед публикацией.")
            
        full_message = create_message(payload=message) # Использует create_message
        
        # 🔥 ИЗМЕНЕНИЕ: Используем кастомный default для msgpack.dumps для обработки UUID и datetime
        message_body = msgpack.dumps(full_message, default=msgpack_default, use_bin_type=True) 

        exchange = await self.channel.get_exchange(exchange_name)
        
        await exchange.publish(
            aio_pika.Message(body=message_body, content_type="application/msgpack"), 
            routing_key=routing_key
        )
        logger.debug(f"Сообщение опубликовано в exchange '{exchange_name}' с ключом '{routing_key}' (MsgPack)")

    async def consume(self, queue_name: str, callback: callable):
        """
        Начинает потребление сообщений из указанной очереди, передавая их в callback.
        Эта функция запускает потребителя в фоновом режиме.
        """
        if not self.channel or self.channel.is_closed:
            raise ConnectionError("Канал RabbitMQ не активен или закрыт. Вызовите connect() перед потреблением.")

        queue = await self.channel.get_queue(queue_name)
        logger.info(f"Начинаем потребление из очереди: {queue_name}")

        consumer_task = asyncio.create_task(
            queue.consume(callback, no_ack=False) 
        )
        self._consumer_tasks.append(consumer_task) 

        logger.info(f"Потребитель для очереди '{queue_name}' запущен в фоновом режиме.")

    async def declare_queue(self, name: str, durable: bool = True, arguments: Optional[Dict[str, Any]] = None):
        """Объявляет очередь."""
        if not self.channel: raise ConnectionError("Канал RabbitMQ не активен.")
        return await self.channel.declare_queue(name=name, durable=durable, arguments=arguments)

    async def declare_exchange(self, name: str, type: str = 'topic', durable: bool = True):
        """Объявляет обменник."""
        if not self.channel: raise ConnectionError("Канал RabbitMQ не активен.")
        return await self.channel.declare_exchange(name=name, type=type, durable=durable)

    async def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Привязывает очередь к обменнику."""
        if not self.channel: raise ConnectionError("Канал RabbitMQ не активен.")
        queue = await self.channel.get_queue(queue_name)
        await queue.bind(exchange_name, routing_key)

    async def _setup_rpc(self):
        """
        Создает эксклюзивную очередь для получения ответов на RPC-вызовы
        и запускает для нее потребителя.
        """
        logger.info("Настройка инфраструктуры для RPC...")
        self._rpc_callback_queue = await self.channel.declare_queue(exclusive=True)
        await self._rpc_callback_queue.consume(self._on_rpc_response)
        logger.info(f"✅ Инфраструктура RPC настроена. Очередь для ответов: {self._rpc_callback_queue.name}")

    async def _on_rpc_response(self, message: IncomingMessage):
        """
        Внутренний обработчик для RPC-ответов. Находит соответствующий future
        по correlation_id и передает в него результат.
        """
        await message.ack()
        correlation_id = message.correlation_id
        if correlation_id in self._rpc_futures:
            future = self._rpc_futures.pop(correlation_id)
            future.set_result(message.body)
        else:
            logger.warning(f"Получен RPC-ответ с неизвестным correlation_id: {correlation_id}")
            
    async def call_rpc(self, queue_name: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """
        Выполняет RPC-вызов: отправляет сообщение и ждет ответа.
        """
        if not self.channel or not self._rpc_callback_queue:
            raise ConnectionError("RPC не настроен. Убедитесь, что MessageBus подключен.")

        correlation_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self._rpc_futures[correlation_id] = future
        
        # 🔥 ИЗМЕНЕНИЕ: Используем кастомный default для msgpack.dumps здесь тоже
        message_body = msgpack.dumps(payload, default=msgpack_default, use_bin_type=True) 

        logger.debug(f"Выполнение RPC-вызова в очередь '{queue_name}' с correlation_id: {correlation_id}")

        await self.channel.default_exchange.publish(
            Message(
                body=message_body,
                content_type="application/msgpack",
                correlation_id=correlation_id,
                reply_to=self._rpc_callback_queue.name,
            ),
            routing_key=queue_name,
        )

        try:
            result_body = await asyncio.wait_for(future, timeout=timeout)
            return msgpack.unpackb(result_body, raw=False)
        except asyncio.TimeoutError:
            self._rpc_futures.pop(correlation_id, None)
            logger.error(f"Таймаут RPC-вызова к очереди '{queue_name}' (correlation_id: {correlation_id})")
            raise TimeoutError(f"RPC call to '{queue_name}' timed out")
        except Exception as e:
            self._rpc_futures.pop(correlation_id, None)
            logger.error(f"Ошибка во время RPC-вызова: {e}", exc_info=True)
            raise

    async def close(self):
        """
        Закрывает соединение с RabbitMQ и отменяет все активные задачи потребителей.
        """
        for task in self._consumer_tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._consumer_tasks, return_exceptions=True) 
        self._consumer_tasks.clear()

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто.")
        else:
            logger.info("Соединение с RabbitMQ уже закрыто или не было установлено.")
