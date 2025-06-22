import asyncio
import uuid
from typing import Dict, Any, Optional, Type
from arq.connections import ArqRedis # Для типизации arq_redis_client


# NEW IMPORT: ConfigProvider
from game_server.config.provider import config

# ИМПОРТ ИНТЕРФЕЙСОВ ДЛЯ МЕНЕДЖЕРОВ (для типизации)
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import ITaskQueueCacheManager # ИЗМЕНЕНО: используем интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient # ИЗМЕНЕНО: для типизации, если нужно
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import IReferenceDataReader # ДОБАВЛЕНО: если нужен
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # ДОБАВЛЕНО: если нужен



from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches

from .base_handler import ICommandHandler
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class AutoExploringHandler(ICommandHandler):
    """ Обработчик для команды 'process_auto_exploring'. """

    # ИЗМЕНЕНО: Конструктор принимает dependencies
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies) # Вызов конструктора базового класса ICommandHandler
        self.logger = dependencies['logger'] # Получаем логгер из зависимостей
        
        # ИЗВЛЕКАЕМ ВСЕ НЕОБХОДИМЫЕ ЗАВИСИМОСТИ ИЗ СЛОВАРЯ dependencies
        self.task_queue_cache_manager: ITaskQueueCacheManager = dependencies['task_queue_cache_manager']
        self.arq_redis_client: ArqRedis = dependencies['arq_redis_client'] # Получаем arq_redis_client напрямую
        self.central_redis_client: CentralRedisClient = dependencies['central_redis_client'] # Если нужен здесь
        self.reference_data_reader: IReferenceDataReader = dependencies['reference_data_reader'] # Если нужен
        self.repository_manager: RepositoryManager = dependencies['repository_manager'] # Если нужен

        self.logger.info("✅ AutoExploringHandler инициализирован.")

    async def execute(self, payload: Dict[str, Any]) -> None:
        character_ids = payload.get("character_ids", [])
        if not character_ids:
            self.logger.warning("AutoExploringHandler: получен пустой список ID персонажей. Пропускаем обработку.")
            return

        self.logger.info(f"AutoExploringHandler: получено {len(character_ids)} ID для обработки.")

        # 1. Получаем свой размер батча и имя ARQ-задачи из общих конфигов
        category_name = "auto_exploring"
        
        batch_size = config.settings.runtime.BATCH_SIZES.get(category_name, config.settings.runtime.DEFAULT_BATCH_SIZE)
        arq_task_name = config.constants.coordinator.ARQ_COMMAND_TASK_NAMES.get(category_name) 

        if not arq_task_name:
            self.logger.error(f"Для категории '{category_name}' не найдено имя ARQ-задачи в константах. Пропускаем.")
            return

        # 2. Готовим инструкции
        instructions = [{"character_id": char_id, "task_type": category_name} for char_id in character_ids]

        # 3. Делим на батчи и отправляем
        successful_batches = 0
        failed_batches = 0
        for batch_data in split_into_batches(instructions, batch_size): 
            try:
                redis_worker_batch_id = str(uuid.uuid4()) # Генерируем UUID здесь
                # ИЗМЕНЕНО: ИСПОЛЬЗУЕМ self.task_queue_cache_manager
                success = await self.task_queue_cache_manager.add_task_to_queue(
                    batch_id=redis_worker_batch_id,
                    key_template=config.constants.coordinator.TICK_WORKER_BATCH_KEY_TEMPLATE, 
                    specs=batch_data, 
                    target_count=len(batch_data),
                    initial_status="pending"
                )
                
                if success:
                    # ИЗМЕНЕНО: ИСПОЛЬЗУЕМ self.arq_redis_client
                    await self.arq_redis_client.enqueue_job(
                        task_name=arq_task_name,
                        batch_id=redis_worker_batch_id
                    )
                    successful_batches += 1
                    self.logger.debug(f"Задача '{arq_task_name}' с batch_id '{redis_worker_batch_id}' поставлена в очередь ARQ. ({len(batch_data)} инструкций)")
                else:
                    failed_batches += 1
                    self.logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' в Redis. ARQ-задача не будет отправлена.")
            except Exception as e:
                failed_batches += 1
                self.logger.error(f"Ошибка при обработке батча для '{category_name}' (инструкций: {len(batch_data)}): {e}", exc_info=True)
        
        if successful_batches > 0:
            self.logger.info(f"AutoExploringHandler: Обработано. Поставлено {successful_batches} батчей задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        elif failed_batches > 0:
            self.logger.error(f"AutoExploringHandler: Ошибка при обработке. Не удалось поставить ни одного батча '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        else:
            self.logger.info("AutoExploringHandler: Задачи для обработки не сформированы или батчи пусты.")