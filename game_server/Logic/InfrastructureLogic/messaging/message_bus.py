#game_server\Logic\InfrastructureLogic\messaging\message_bus.py

import asyncio
from typing import Dict, Any, AsyncIterator
from arq.connections import ArqRedis

# 🔥 ИЗМЕНЕНИЕ: Вместо json импортируем msgpack
import msgpack

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger
from .message_format import create_message


class RedisMessageBus:
    """
    Реализация шины сообщений на базе Redis Streams.
    Использует MsgPack для быстрой и компактной сериализации.
    """
    def __init__(self, redis_pool: ArqRedis):
        self.redis = redis_pool
        logger.info("✅ RedisMessageBus (с MsgPack) инициализирован.")

    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Публикует сообщение в указанный канал (стрим) Redis.
        Сериализует payload с помощью MsgPack.
        """
        full_message = create_message(payload=message)
        payload_to_publish = full_message.get("payload", {})
        
        # 🔥 ИЗМЕНЕНИЕ: Используем msgpack.packb для сериализации в байты
        # packb = pack to bytes
        packed_payload = msgpack.packb(payload_to_publish, use_bin_type=True)
        
        await self.redis.xadd(channel, {'payload': packed_payload})
        logger.debug(f"Сообщение опубликовано в канал '{channel}'")

    async def subscribe(self, channel: str, last_id: str = '$') -> AsyncIterator[Dict[str, Any]]:
        """
        Подписывается на канал (стрим) и асинхронно возвращает новые сообщения.
        Десериализует payload с помощью MsgPack.
        """
        logger.info(f"Подписка на канал '{channel}'...")
        while True:
            try:
                # Ожидаем новое сообщение в стриме
                messages = await self.redis.xread(
                    streams={channel: last_id},
                    count=1,
                    block=0 # Блокирующий вызов, ждет вечно
                )
                
                for stream, message_list in messages:
                    for message_id, raw_message in message_list:
                        if b'payload' in raw_message:
                            # 🔥 ИЗМЕНЕНИЕ: Используем msgpack.unpackb для десериализации из байтов
                            # unpackb = unpack from bytes
                            payload = msgpack.unpackb(raw_message[b'payload'], raw=False)
                            yield payload
                        
                        # Обновляем ID последнего полученного сообщения
                        last_id = message_id

            except ConnectionError:
                logger.error(f"Потеряно соединение с Redis в MessageBus. Попытка переподключения...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Ошибка в подписчике MessageBus: {e}", exc_info=True)
                await asyncio.sleep(1)