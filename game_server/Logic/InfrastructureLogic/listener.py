
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.services.logging.logging_setup import logger


import json

from game_server.settings import REDIS_CHANNELS

class RedisListener:
    """Менеджер подписки на Redis-каналы и обработку сообщений."""

    def __init__(self):
        self.redis_client = CentralRedisClient().redis  # ✅ Используем объект Redis напрямую
        

    async def start_listening(self):
        """Запускает подписку на каналы и обработку сообщений."""
        pubsub = self.redis_client.pubsub()

        try:
            # Подписываемся на все каналы и логируем успешную подписку как info
            logger.info(f"📡 Подписка на каналы: {REDIS_CHANNELS}")
            await pubsub.subscribe(*REDIS_CHANNELS.values())
            logger.info(f"🔔 Подписка на каналы: {', '.join(REDIS_CHANNELS.values())}")

            async for message in pubsub.listen():
                msg_type = message.get("type")
                if msg_type == "message":
                    await self.process_message(message["channel"], message["data"])
                elif msg_type == "subscribe":
                    # Здесь вместо warning выводим info о подтверждении подписки
                    channel = message.get("channel")
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    logger.info(f"✅ Подписка подтверждена для канала: {channel}")
                else:
                    logger.warning(f"⚠️ Неожиданный тип сообщения: {message}")

        except Exception as e:
            logger.error(f"❌ Ошибка в слушателе: {e}")

    async def process_message(self, channel, data):
        """Универсальный обработчик сообщений по каналам."""
        # Проверяем тип, чтобы декодировать только байты
        channel = channel.decode() if isinstance(channel, bytes) else channel
        if isinstance(data, bytes):
            data = data.decode()
        # Если data уже строка или даже дикт – оставляем как есть, либо превращаем в строку
        elif not isinstance(data, (str, dict)):
            data = str(data)

        logger.info(f"📩 Получено `{data}` из `{channel}`")

        # Динамическое распределение по каналам
        handlers = {
            REDIS_CHANNELS["coordinator"]: self.process_message_coordinator,
            REDIS_CHANNELS["worker"]: self.process_message_worker,
            REDIS_CHANNELS["tasks"]: self.process_message_tasks,
            REDIS_CHANNELS["alerts"]: self.process_message_alerts,
            REDIS_CHANNELS["system"]: self.process_message_system,
        }

        handler = handlers.get(channel)
        if handler:
            await handler(data)
        else:
            logger.warning(f"⚠️ Неизвестный канал: {channel}")


        # Обработчик сообщений, поступающих с канала координатора
    async def process_message_coordinator(self, data):
        """Обрабатывает сообщения от координатора, но игнорирует сообщения от самого listener."""
        
        # Проверяем, если сообщение пришло от самого listener — просто выходим
        if data in ["new_tasks", "shutdown"]:  # Добавь нужные исключения
            logger.info(f"🔄 Игнорируем сообщение `{data}` от listener")
            return

        # Просто обновляем флаг без обработки JSON
        await self.redis_client.set("coordinator_status", data)
        logger.info(f"🛑 Координатор обновил статус на `{data}` (без JSON, без пересылки сообщений)")



    # Обработчик сообщений от воркеров
    async def process_message_worker(self, data):
        """Обрабатывает сообщения от воркеров: если приходит 'check_report', передаёт его координатору."""
        # Если данные представлены в виде байтов, декодируем их в строку
        data = data.decode() if isinstance(data, bytes) else data

        # Если сообщение равно 'check_report', пересылаем соответствующую команду координатору
        if data == "check_report":
            await self.redis_client.publish(
                REDIS_CHANNELS["coordinator"],
                json.dumps({"command": "check_report"})
            )
            logger.info("📩 Получено 'check_report' от воркеров, отправлено координатору.")
        # Если сообщение не соответствует ожидаемому, логируем предупреждение
        else:
            logger.warning(f"⚠️ Неожиданное сообщение от воркеров: {data}")


    # Обработчик сообщений в канале tasks
    async def process_message_tasks(self, data):
        """Читаем `tasks`, получаем `new_tasks`, проверяем статус и передаём в `coordinator` если нужно."""
        # Если данные представлены в виде байтов, декодируем их в строку
        data = data.decode() if isinstance(data, bytes) else data

        # Получаем текущий статус координатора из Redis
        coordinator_status = await self.redis_client.get("coordinator_status")
        # Если статус получен, декодируем его; если нет — считаем, что координатор в состоянии "sleeping"
        coordinator_status = coordinator_status.decode() if coordinator_status else "sleeping"

        # Если полученное сообщение равно "new_tasks"
        if data == "new_tasks":
            # Если координатор "спит" или находится в режиме проверки репортов, пересылаем сообщение координатору
            if coordinator_status in ["sleeping", "checking_reports"]:
                await self.redis_client.publish(REDIS_CHANNELS["coordinator"], "new_tasks")
                logger.info(f"🚀 Получено `new_tasks`, статус `{coordinator_status}`, отправлено координатору.")
            else:
                # Если координатор уже занят, просто фиксируем факт, но не передаём сообщение
                logger.info(f"⏳ `new_tasks` пришло, но координатор уже `{coordinator_status}`, ничего не делаем.")
        else:
            # Если сообщение не соответствует ожидаемому формату, логируем предупреждение
            logger.warning(f"⚠️ Неожиданное сообщение от `tasks`: {data}")


    # Обработчик системных сообщений
    async def process_message_system(self, data):
        """Обрабатывает системные сообщения: если 'shutdown', передаёт его ключевым каналам, но НЕ alerts."""
        # Если данные представлены в виде байтов, декодируем их
        data = data.decode() if isinstance(data, bytes) else data

        # Если сообщение равно "shutdown"
        if data == "shutdown":
            shutdown_message = json.dumps({"command": "shutdown"})

            # Рассылаем команду 'shutdown' по ключевым каналам (не включая alerts)
            for channel in ["coordinator", "tasks", "worker"]:
                await self.redis_client.publish(REDIS_CHANNELS[channel], shutdown_message)

            logger.info("🛑 Получено 'shutdown' из system_channel! Команда отправлена координатору, воркерам и таскам.")
        else:
            # При получении неизвестного системного сообщения логируем предупреждение
            logger.warning(f"⚠️ Неожиданное сообщение в system_channel: {data}")




    async def process_message_alerts(self, data):
        logger.info(f"🛑 Заглушка вызвана для alerts: {data}")  # Пока просто логируем сообщение






if __name__ == "__main__":
    import asyncio
    listener = RedisListener()
    
    async def main():
        await listener.start_listening()
        logger.info("🚀 Слушатель Redis запущен и готов к работе!")
    
    asyncio.run(main())  # 🚀 Запускаем воркер с RedisListener
