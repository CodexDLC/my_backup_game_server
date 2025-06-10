# coordinator_tick/tick_coordinator.py

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional

# Импорты из вашего оригинального Coordinator
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from .collector.tick_collector import Collector

# Импортируем наш обновленный TaskProcessor
from .coordinator.tick_task_processor import TaskProcessor

from .tick_utils.tick_logger import logger

# Импортируем RabbitMQ очередь и TTL
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import RABBITMQ_QUEUE_TICK_WORKER, BATCH_TASK_TTL_SECONDS
# НОВАЯ КОНСТАНТА: Очередь для команд Координатору
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import COORDINATOR_COMMAND_QUEUE

# НОВЫЕ ИМПОРТЫ
# Импортируем наш универсальный TaskDispatcher
from game_server.Logic.InfrastructureLogic.messaging.rabbit_utils import TaskDispatcher
# Импортируем нашу новую Celery-задачу для тиков
from game_server.Logic.InfrastructureLogic.celery.task.tasks_tick_processing import process_tick_batch_task
# Импортируем наш центральный RabbitMQClient
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_client import rabbitmq_client as central_rabbitmq_client


class Coordinator:
    def __init__(self):
        """
        Конструктор Координатора.
        Инициализирует все необходимые компоненты-обработчики.
        """
        self.processing_lock = asyncio.Lock()
        self.redis = CentralRedisClient()
        
        self.task_dispatcher = TaskDispatcher()
        self.rabbitmq_client = central_rabbitmq_client
        
        self.collector = Collector()
        self.task_processor = TaskProcessor(redis=self.redis) 
        
        self.active_tasks = []
        self._command_consumer_task: Optional[asyncio.Task] = None

        self.logger = logger
        self.logger.info("✅ Координатор инициализирован.")

    async def _listen_for_rabbitmq_commands(self):
        """
        Слушает очередь RabbitMQ на предмет входящих команд для Координатора.
        """
        try:
            # 🔥 ИЗМЕНЕНИЕ: УДАЛЯЕМ ПОВТОРНЫЙ ВЫЗОВ connect() 🔥
            # await self.rabbitmq_client.connect() 
            
            channel = self.rabbitmq_client._channel
            if not channel:
                self.logger.error("❌ Не удалось получить канал RabbitMQ для прослушивания команд.")
                return

            command_queue = await channel.declare_queue(
                COORDINATOR_COMMAND_QUEUE,
                durable=True
            )
            self.logger.info(f"✅ Координатор слушает RabbitMQ очередь команд: '{COORDINATOR_COMMAND_QUEUE}'")

            async with command_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            command_data = json.loads(message.body.decode('utf-8'))
                            command = command_data.get('command')
                            data = command_data.get('data')

                            if command:
                                self.logger.info(f"Получена RabbitMQ команда: {command} с данными: {data}")
                                await self.handle_command(command, data)
                            else:
                                self.logger.warning(f"Получено некорректное сообщение команды из RabbitMQ: {command_data}")
                        except json.JSONDecodeError:
                            self.logger.error(f"Получено некорректное JSON сообщение из RabbitMQ: {message.body.decode('utf-8')}")
                        except Exception as e:
                            self.logger.error(f"Ошибка при обработке RabbitMQ команды: {e}", exc_info=True)
        except asyncio.CancelledError:
            self.logger.info("Прослушивание RabbitMQ команд отменено.")
        except Exception as e:
            self.logger.critical(f"❌ Критическая ошибка в RabbitMQ-слушателе команд Координатора: {e}", exc_info=True)


    async def start(self):
        """
        Запускает Координатор и его компоненты.
        """
        self.logger.info("✅ Redis-клиент Координатора инициализирован.")

        await self.rabbitmq_client.connect()
        self.logger.info("✅ RabbitMQClient Координатора подключен.")

        self._command_consumer_task = asyncio.create_task(self._listen_for_rabbitmq_commands())
        self.active_tasks.append(self._command_consumer_task)

        self.logger.info("✅ Координатор успешно запущен. Ожидает команды.")
        await asyncio.gather(*self.active_tasks)

    async def stop(self):
        """Останавливает компоненты координатора."""
        self.logger.info("🛑 Остановка Координатора...")

        for task in self.active_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if not self.redis._using_external_redis:
             await self.redis.close()
        self.logger.info("👋 Redis-клиент Координатора отключен.")
        
        await self.rabbitmq_client.close()
        self.logger.info("👋 RabbitMQClient Координатора отключен.")

        self.logger.info("Координатор остановлен.")

    async def handle_command(self, command: str, data: dict = None):
        """
        Обрабатывает входящие команды.
        На данном этапе обрабатывается только команда "run_collector".
        """
        if self.processing_lock.locked():
            self.logger.warning(f"Команда '{command}' получена, но обработка уже идет. Проигнорирована.")
            return

        async with self.processing_lock:
            self.logger.info(f"Получена и заблокирована команда: {command} с данными: {data}")

            if command == "run_collector":
                raw_tasks_by_category = await self.collector.run_collector()
                
                if raw_tasks_by_category:
                    self.logger.info("Coordinator: Получены задачи от Collector, передача в TaskProcessor для батчинга...")
                    
                    created_batch_info_list = await self.task_processor.prepare_and_process_batches(raw_tasks_by_category)
                    
                    if created_batch_info_list:
                        self.logger.info(f"Coordinator: TaskProcessor создал {len(created_batch_info_list)} батчей. Отправляем ID батчей в RabbitMQ через TaskDispatcher...")
                        
                        for batch_info in created_batch_info_list:
                            batch_id = batch_info['batch_id']
                            category = batch_info['category']
                            
                            await self.task_dispatcher.dispatch_existing_batch_id(
                                batch_id=batch_id,
                                category=category,
                                celery_queue_name=RABBITMQ_QUEUE_TICK_WORKER,
                                celery_task_callable=process_tick_batch_task,
                                task_type_name="тиков"
                            )

                    else:
                        self.logger.info("Coordinator: TaskProcessor не создал батчей для отправки.")
                else:
                    self.logger.info("Coordinator: Collector не вернул задач для обработки.")
            
            elif command == "shutdown":
                self.logger.info("Команда на отключение. Завершение работы...")
                for task in self.active_tasks:
                    task.cancel()
            else:
                self.logger.warning(f"Получена неизвестная или временно не обрабатываемая команда: {command}. Проигнорирована.")

            self.logger.info(f"Обработка команды '{command}' завершена. Блокировка снята.")

# --- ТОЧКА ВХОДА ДЛЯ САМОСТОЯТЕЛЬНОГО ПРОЦЕССА ---
async def main():
    coordinator = Coordinator()
    try:
        await coordinator.start()
    except ConnectionError:
        logger.critical("Не удалось запустить Координатор из-за проблем с подключением. Выход.")
    except asyncio.CancelledError:
        logger.info("Координатор был отменен.")
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка в основном цикле Координатора: {e}", exc_info=True)
    finally:
        await coordinator.stop()
        logger.info("Координатор завершил свою работу.")

if __name__ == "__main__":
    asyncio.run(main())