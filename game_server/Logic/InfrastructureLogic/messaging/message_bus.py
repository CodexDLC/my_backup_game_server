# game_server/Logic/InfrastructureLogic/messaging/message_bus.py

import asyncio
from typing import Dict, Any, AsyncIterator
from arq.connections import ArqRedis
import msgpack

from game_server.config.logging.logging_setup import app_logger as logger
# ИЗМЕНЕНО: Импортируем наш новый интерфейс и форматтер сообщений
from .i_message_bus import IMessageBus
from .message_format import create_message

# ИЗМЕНЕНО: Класс теперь реализует интерфейс IMessageBus
class RedisMessageBus(IMessageBus):
    """
    Реализация шины сообщений на базе Redis Streams.
    Полностью реализует интерфейс IMessageBus.
    """
    def __init__(self, redis_pool: ArqRedis):
        self.redis = redis_pool
        logger.info("✅ RedisMessageBus (совместимый с IMessageBus) инициализирован.")

    # ИЗМЕНЕНО: Сигнатура метода теперь соответствует интерфейсу
    async def publish(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """
        Публикует полное сообщение (metadata + payload) в стрим Redis.

        Для Redis Streams мы используем `routing_key` как имя стрима.
        `exchange_name` игнорируется, так как у Redis нет такой концепции.
        """
        # 1. Создаем полный "конверт" для сообщения
        full_message = create_message(payload=message)
        
        # 2. Сериализуем ВЕСЬ "конверт", а не только payload
        packed_message = msgpack.packb(full_message, use_bin_type=True)
        
        # 3. Публикуем в стрим (routing_key - это имя стрима)
        #    Используем ключ 'data' для хранения всего сообщения
        await self.redis.xadd(routing_key, {'data': packed_message})
        logger.debug(f"Сообщение {full_message['metadata']['message_id']} опубликовано в стрим '{routing_key}'")

    # ИЗМЕНЕНО: Сигнатура метода теперь соответствует интерфейсу
    async def subscribe(self, queue_name: str, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        Подписывается на стрим (имя которого передается в queue_name)
        и асинхронно возвращает полные сообщения.
        """
        last_id = kwargs.get("last_id", "$")
        logger.info(f"Подписка на стрим '{queue_name}'...")
        while True:
            try:
                messages = await self.redis.xread(
                    streams={queue_name: last_id},
                    count=1,
                    block=0 
                )
                
                for stream, message_list in messages:
                    for message_id, raw_message in message_list:
                        # ИЗМЕНЕНО: Ожидаем ключ 'data', а не 'payload'
                        if b'data' in raw_message:
                            # Десериализуем и возвращаем ВЕСЬ "конверт"
                            full_message = msgpack.unpackb(raw_message[b'data'], raw=False)
                            yield full_message
                        
                        last_id = message_id

            except ConnectionError:
                logger.error(f"Потеряно соединение с Redis в MessageBus. Попытка переподключения...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Ошибка в подписчике MessageBus: {e}", exc_info=True)
                await asyncio.sleep(1)