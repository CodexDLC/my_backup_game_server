from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import listener_logger as logger
import os
from game_server.app_cache.redis_client import RedisClient

# Получаем название канала из переменной окружения или используем значение по умолчанию
REDIS_CHANNELS = {
    "tasks": os.getenv("REDIS_TASKS_CHANNEL", "task_channel")  # ✅ Канал для задач
}

class CollectorListener:
    def __init__(self):
        """Инициализация слушателя, подписка на канал задач."""
        self.redis_client = RedisClient()  # ✅ Используем RedisClient для работы с Redis        self.channel_name = REDIS_CHANNELS["tasks"]
        self.pubsub_channel = None

    async def connect(self):
        """Подключается к Redis и подписывается на канал задач."""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.channel_name)
        self.pubsub_channel = pubsub
        logger.info(f"✅ Подписано на канал задач: {self.channel_name}")

    async def shutdown(self):
        """Закрывает соединение с Redis перед остановкой слушателя."""
        logger.info("🛑 Завершаем работу, отключаемся от Redis...")
        await self.redis_client.close()
        logger.info("✅ Соединение с Redis закрыто.")
