# coordinator_tick/coordinator/tick_coordinator_listener.py

from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger  # Импортируем логгер
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
import asyncio
import os
from typing import Callable, Optional # Добавлен импорт Callable и Optional


# Получаем название канала из переменной окружения или используем значение по умолчанию
REDIS_CHANNELS = {
    "coordinator": os.getenv("REDIS_COORDINATOR_CHANNEL", "coordinator_channel")
}

class CoordinatorListener:
    # 🔥 ИЗМЕНЕНИЕ: __init__ теперь принимает command_handler и redis_client 🔥
    def __init__(self, command_handler: Callable, redis_client: CentralRedisClient):
        """
        Инициализация слушателя, подписка на канал координатора.
        :param command_handler: Функция обратного вызова для обработки полученных команд.
        :param redis_client: Экземпляр CentralRedisClient.
        """
        self.redis_client = redis_client # Теперь используем переданный Redis-клиент
        self.channel_name = REDIS_CHANNELS["coordinator"]
        self.pubsub_channel: Optional[asyncio.channels.PubSub] = None # Уточняем тип
        self.command_handler = command_handler # Сохраняем обработчик команд

    async def connect(self):
        """Подключается к Redis и подписывается на канал координатора."""
        # Убедимся, что redis_client подключен, если он не был подключен до этого
        # В нашем случае Coordinator подключает его в своем start() методе.
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.channel_name)
        self.pubsub_channel = pubsub
        logger.info(f"Подписано на канал: {self.channel_name}")

    # 🔥 ИЗМЕНЕНИЕ: Метод run() заменяет listen(), и не требует callback в параметрах,
    # так как callback уже сохранен в self.command_handler 🔥
    async def run(self):
        """Слушает канал и передаёт команды в обработчик."""
        await self.connect() # Подключаемся при запуске run()
        logger.info(f"Начало прослушивания канала Redis: {self.channel_name}")
        try:
            while True:
                # get_message с ignore_subscribe_messages=True
                message = await self.pubsub_channel.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    msg_data = message["data"]

                    if isinstance(msg_data, bytes):
                        msg_data = msg_data.decode("utf-8")

                    logger.info(f"Получено сообщение: {msg_data}")
                    # 🔥 Вызываем сохраненный обработчик команд 🔥
                    await self.command_handler(msg_data)

                await asyncio.sleep(1) # Задержка для предотвращения перегрузки ЦПУ
        except asyncio.CancelledError:
            logger.info(f"Прослушивание канала {self.channel_name} отменено.")
        except Exception as e:
            logger.error(f"Ошибка при прослушивании канала Redis: {str(e)}", exc_info=True)
        finally:
            await self.shutdown() # Вызываем shutdown при завершении

    async def shutdown(self):
        """Закрывает подписку и очищает соединение."""
        if self.pubsub_channel:
            await self.pubsub_channel.unsubscribe(self.channel_name)
            logger.info(f"🔴 Отписка от канала {self.channel_name}")
            self.pubsub_channel = None  # Удаляем ссылку
        # НЕ ЗАКРЫВАЕМ redis_client здесь, так как он управляется Coordinator'ом