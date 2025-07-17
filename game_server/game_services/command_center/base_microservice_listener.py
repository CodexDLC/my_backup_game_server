# game_server\game_services\command_center\base_microservice_listener.py

import asyncio
import msgpack
from typing import Dict, Any, Optional, Callable # Type больше не нужен для конфига
import logging 
import inject

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from aio_pika import IncomingMessage
# from game_server.config.logging.logging_setup import app_logger as logger # Больше не нужен


class BaseMicroserviceListener:
    """
    Базовый класс для микросервисов-потребителей RabbitMQ.
    Управляет жизненным циклом (старт/стоп) и применяет политики обработки,
    такие как ограничение параллелизма и таймауты.
    Зависимости внедряются через @inject.autoparams.
    Константы конфигурации (QUEUE, TASKS_LIMIT, TIMEOUT) ожидаются в классе-наследнике.
    """
    @inject.autoparams()
    # 🔥 ИЗМЕНЕНО: Тип оркестратора возвращен к Any
    def __init__(self, message_bus: IMessageBus, orchestrator: Any, logger: logging.Logger):
        self.message_bus = message_bus
        self.orchestrator = orchestrator
        self.logger = logger
        self._listen_task: asyncio.Task | None = None
        
        self.SERVICE_QUEUE = getattr(self, 'SERVICE_QUEUE', None)
        self.MAX_CONCURRENT_TASKS = getattr(self, 'MAX_CONCURRENT_TASKS', None)
        self.COMMAND_PROCESSING_TIMEOUT = getattr(self, 'COMMAND_PROCESSING_TIMEOUT', None)

        if self.SERVICE_QUEUE is None or \
           self.MAX_CONCURRENT_TASKS is None or \
           self.COMMAND_PROCESSING_TIMEOUT is None:
            raise NotImplementedError(
                f"Класс {self.__class__.__name__} должен определить константы "
                "SERVICE_QUEUE, MAX_CONCURRENT_TASKS, COMMAND_PROCESSING_TIMEOUT."
            )

        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TASKS)
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с лимитом в {self.MAX_CONCURRENT_TASKS} задач.")

    def start(self):
        if self._listen_task is None or self._listen_task.done():
            self.logger.info(f"Запуск {self.__class__.__name__}...")
            self._listen_task = asyncio.create_task(self._listen_loop())
        else:
            self.logger.warning(f"{self.__class__.__name__} уже запущен.")

    async def stop(self):
        if self._listen_task and not self._listen_task.done():
            self.logger.info(f"Остановка {self.__class__.__name__}...")
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"{self.__class__.__name__} успешно остановлен.")

    async def _listen_loop(self):
        self.logger.info(f"🎧 {self.__class__.__name__} начинает прослушивание очереди '{self.SERVICE_QUEUE}'")
        try:
            await self.message_bus.consume(self.SERVICE_QUEUE, self._on_message_received_callback)
            await asyncio.Future()
            
        except asyncio.CancelledError:
            self.logger.info("Цикл прослушивания был отменен.")
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в цикле прослушивания {self.__class__.__name__}: {e}", exc_info=True)
            await asyncio.sleep(5)

    async def _on_message_received_callback(self, message: IncomingMessage):
        processed_message_dict: Optional[Dict[str, Any]] = None
        try:
            processed_message_dict = msgpack.unpackb(message.body, raw=False)
            await self._dispatch_command(processed_message_dict, message)
            await message.ack()
            self.logger.debug(f"Сообщение {message.delivery_tag} из очереди '{self.SERVICE_QUEUE}' успешно обработано (ACK).")

        except asyncio.CancelledError:
            self.logger.info(f"Обработка сообщения {message.delivery_tag} отменена.")
        except Exception as e:
            msg_id = processed_message_dict.get("metadata", {}).get("message_id", "N/A") if processed_message_dict is not None else "N/A"
            self.logger.error(f"Ошибка при обработке сообщения {msg_id} из очереди '{self.SERVICE_QUEUE}': {e}", exc_info=True)
            await message.nack(requeue=False)

    async def _dispatch_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        async with self.semaphore:
            try:
                await asyncio.wait_for(
                    self._process_single_command(message_data, original_message),
                    timeout=self.COMMAND_PROCESSING_TIMEOUT
                )
            except Exception as e:
                msg_id = message_data.get("metadata", {}).get("message_id", "N/A")
                self.logger.error(f"Ошибка или таймаут при обработке команды {msg_id} в _dispatch_command: {e}", exc_info=True)
                raise 


    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        raise NotImplementedError("Метод _process_single_command должен быть реализован в дочернем классе")