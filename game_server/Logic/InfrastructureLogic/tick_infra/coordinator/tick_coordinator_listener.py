from game_server.Logic.DataAccessLogic.db_in import AsyncDatabase
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger  # Импортируем логгер


import asyncio
import os
from game_server.app_cache.redis_client import RedisClient


# Получаем название канала из переменной окружения или используем значение по умолчанию
REDIS_CHANNELS = {
    "coordinator": os.getenv("REDIS_COORDINATOR_CHANNEL", "coordinator_channel")
}

class CoordinatorListener:
    def __init__(self):
        """Инициализация слушателя, подписка на канал координатора."""
        self.redis_client = RedisClient()
        self.channel_name = REDIS_CHANNELS["coordinator"]
        self.pubsub_channel = None

    async def connect(self):
        """Подключается к Redis и подписывается на канал координатора."""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.channel_name)
        self.pubsub_channel = pubsub
        logger.info(f"Подписано на канал: {self.channel_name}")

    async def listen(self, callback):
        """Слушает канал и передаёт команды в обработчик."""
        while True:
            message = await self.pubsub_channel.get_message(ignore_subscribe_messages=True)
            if message and message["type"] == "message":
                msg_data = message["data"]

                if isinstance(msg_data, bytes):
                    msg_data = msg_data.decode("utf-8")

                logger.info(f"Получено сообщение: {msg_data}")
                await callback(msg_data)

            await asyncio.sleep(1)

    async def shutdown(self):
        """Закрывает подписку и очищает соединение."""
        if self.pubsub_channel:
            await self.pubsub_channel.unsubscribe(self.channel_name)
            logger.info(f"🔴 Отписка от канала {self.channel_name}")
            self.pubsub_channel = None  # Удаляем ссылку



