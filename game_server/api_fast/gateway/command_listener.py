# api_fast/gateway/command_listener.py
import asyncio
import msgpack
from typing import Dict
import redis.asyncio as aioredis

# 👈 ИЗМЕНЕНИЕ: Используем ваш глобальный логгер
from game_server.api_fast.gateway.connection_manager import ConnectionManager
from game_server.api_fast.gateway.gateway_config import GATEWAY_CONSUMER_GROUP_NAME, GATEWAY_CONSUMER_NAME, GATEWAY_LISTEN_STREAMS
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger




class CommandListener:
    """
    Основной сервис шлюза, который слушает Redis Streams и передает команды боту.
    """
    def __init__(self, redis_client: aioredis.Redis, connection_manager: ConnectionManager):
        # 👈 Убираем создание локального логгера
        self.redis = redis_client
        self.connection_manager = connection_manager
        self.streams_to_listen = {stream: '>' for stream in GATEWAY_LISTEN_STREAMS}
        self.is_running = False
        logger.info("✅ CommandListener инициализирован.")

    async def _ensure_consumer_groups_exist(self):
        """При старте проверяет и создает Consumer Group, если их нет."""
        for stream in self.streams_to_listen.keys():
            try:
                await self.redis.xgroup_create(stream, GATEWAY_CONSUMER_GROUP_NAME, id='0', mkstream=True)
                logger.info(f"Создана новая Consumer Group '{GATEWAY_CONSUMER_GROUP_NAME}' для стрима '{stream}'.")
            except aioredis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.debug(f"Consumer Group '{GATEWAY_CONSUMER_GROUP_NAME}' для стрима '{stream}' уже существует.")
                else:
                    raise

    async def listen_forever(self):
        """Главный цикл прослушивания стримов."""
        await self._ensure_consumer_groups_exist()
        self.is_running = True
        logger.info(f"Слушатель запускается. Целевые стримы: {list(self.streams_to_listen.keys())}")

        while self.is_running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=GATEWAY_CONSUMER_GROUP_NAME,
                    consumername=GATEWAY_CONSUMER_NAME,
                    streams=self.streams_to_listen,
                    count=1,
                    block=0
                )
                if not messages:
                    continue

                for _, message_list in messages:
                    for message_id, raw_message in message_list:
                        try:
                            packed_data = raw_message.get(b'data')
                            if not packed_data:
                                logger.warning(f"Получено сообщение {message_id} без поля 'data'.")
                                continue
                                
                            command = msgpack.unpackb(packed_data, raw=False)
                            await self.connection_manager.send_command(command)
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения {message_id}: {e}", exc_info=True)

            except ConnectionError:
                logger.error("Потеряно соединение с Redis в CommandListener. Попытка переподключения через 5с...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Критическая ошибка в цикле CommandListener: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    def stop(self):
        """Остановка цикла прослушивания."""
        self.is_running = False
        logger.info("Получен сигнал на остановку CommandListener.")