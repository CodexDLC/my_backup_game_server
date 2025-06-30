# game_server\game_services\command_center\base_microservice_listener.py

import asyncio
import msgpack
from typing import Dict, Any, Type, Optional, Callable # Добавлен Callable

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from aio_pika import IncomingMessage
from game_server.config.logging.logging_setup import app_logger as logger


class BaseMicroserviceListener:
    """
    Базовый класс для микросервисов-потребителей RabbitMQ.
    Управляет жизненным циклом (старт/стоп) и применяет политики обработки,
    такие как ограничение параллелизма и таймауты.
    Теперь работает с MsgPack сообщениями и новым API RabbitMQMessageBus.
    """
    def __init__(self, message_bus: IMessageBus, config: Type, orchestrator: Any = None):
        self.message_bus = message_bus
        self.config = config
        self.orchestrator = orchestrator
        self.logger = logger
        self._listen_task: asyncio.Task | None = None
        
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с лимитом в {config.MAX_CONCURRENT_TASKS} задач.")

    def start(self):
        if self._listen_task is None:
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
        self.logger.info(f"🎧 {self.__class__.__name__} начинает прослушивание очереди '{self.config.SERVICE_QUEUE}'")
        try:
            # 🔥 ИЗМЕНЕНИЕ: Передаем _on_message_received_callback напрямую
            # RabbitMQMessageBus.consume вызывает _on_message_received_callback с IncomingMessage
            await self.message_bus.consume(self.config.SERVICE_QUEUE, self._on_message_received_callback)
            
        except asyncio.CancelledError:
            self.logger.info("Цикл прослушивания был отменен.")
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в цикле прослушивания {self.__class__.__name__}: {e}", exc_info=True)
            await asyncio.sleep(5) 

    async def _on_message_received_callback(self, message: IncomingMessage): # message здесь - IncomingMessage
        """
        Колбэк, вызываемый RabbitMQMessageBus для каждого нового сообщения.
        Отвечает за десериализацию, применение политик и подтверждение/отклонение сообщения.
        """
        processed_message_dict: Optional[Dict[str, Any]] = None
        try:
            # Десериализуем сообщение здесь
            # 🔥 ИСПРАВЛЕНИЕ: Используем message.body для десериализации
            processed_message_dict = msgpack.unpackb(message.body, raw=False)
            
            # 🔥 ИЗМЕНЕНИЕ: _dispatch_command теперь получает data и IncomingMessage
            await self._dispatch_command(processed_message_dict, message)
            
            # ACK/NACK всегда делаем здесь, имея доступ к оригинальному 'message'
            await message.ack()
            self.logger.debug(f"Сообщение {message.delivery_tag} из очереди '{self.config.SERVICE_QUEUE}' успешно обработано (ACK).")

        except asyncio.CancelledError:
            self.logger.info(f"Обработка сообщения {message.delivery_tag} отменена.")
            # Если отмена, NACK не требуется, сообщение может быть перепоставлено,
            # если коннект закроется или consumer отвалится.
        except Exception as e:
            msg_id = processed_message_dict.get("metadata", {}).get("message_id", "N/A") if processed_message_dict is not None else "N/A"
            self.logger.error(f"Ошибка при обработке сообщения {msg_id} из очереди '{self.config.SERVICE_QUEUE}': {e}", exc_info=True)
            # 🔥 ИСПРАВЛЕНИЕ: nack делается здесь на оригинальном 'message'
            await message.nack(requeue=False) # Отклоняем сообщение, не перепоставляя его в очередь

    # 🔥 ИЗМЕНЕНИЕ: _dispatch_command теперь принимает message_data и original_message
    async def _dispatch_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Применяет политики (семафор, таймаут) и вызывает конкретный обработчик.
        Передает оригинальное сообщение в _process_single_command.
        """
        async with self.semaphore:
            try:
                await asyncio.wait_for(
                    # 🔥 ИЗМЕНЕНИЕ: _process_single_command теперь получает data и original_message
                    self._process_single_command(message_data, original_message),
                    timeout=self.config.COMMAND_PROCESSING_TIMEOUT
                )
            except Exception as e:
                msg_id = message_data.get("metadata", {}).get("message_id", "N/A")
                self.logger.error(f"Ошибка или таймаут при обработке команды {msg_id} в _dispatch_command: {e}", exc_info=True)
                # 🔥 ВАЖНО: здесь не делаем nack, так как он уже сделан в _on_message_received_callback
                raise 


    # 🔥 ИЗМЕНЕНИЕ: _process_single_command теперь принимает data и original_message
    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        **Абстрактный метод.** Основная бизнес-логика обработки сообщения.
        Должна быть реализована в дочернем классе.
        message_data: Десериализованный словарь с данными сообщения.
        original_message: Оригинальный объект aio_pika.IncomingMessage для возможных дополнительных действий.
        """
        raise NotImplementedError("Метод _process_single_command должен быть реализован в дочернем классе")