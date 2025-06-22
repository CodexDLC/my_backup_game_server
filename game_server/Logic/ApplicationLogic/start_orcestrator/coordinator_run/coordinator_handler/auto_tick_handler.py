# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_run/coordinator_handler/auto_leveling_handler.py

import uuid
from typing import Dict, Any, Optional, Type

from arq import ArqRedis
# from arq.connections import ArqRedis # УДАЛЕНО: будет получен из зависимостей

# Главный импорт для всей конфигурации
from game_server.config.provider import config

# ИМПОРТ ИНТЕРФЕЙСОВ для менеджеров (для типизации)
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import ITaskQueueCacheManager # ИЗМЕНЕНО: используем интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient # ИЗМЕНЕНО: для типизации, если нужно


from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches

from .base_handler import ICommandHandler
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class AutoLevelingHandler(ICommandHandler):
    """ Обработчик для команды 'process_auto_leveling'. """

    # ИЗМЕНЕНО: Конструктор принимает dependencies
    def __init__(self, dependencies: Dict[str, Any]):
        # super().__init__(dependencies) # Если ICommandHandler требует super().__init__(dependencies), добавьте
        self.logger = dependencies['logger'] # Получаем логгер из зависимостей
        
        # ИЗВЛЕКАЕМ ВСЕ НЕОБХОДИМЫЕ ЗАВИСИМОСТИ ИЗ СЛОВАРЯ dependencies
        self.task_queue_cache_manager: ITaskQueueCacheManager = dependencies['task_queue_cache_manager']
        self.arq_redis_client: ArqRedis = dependencies['arq_redis_client'] # Получаем arq_redis_client напрямую
        # self.central_redis_client: CentralRedisClient = dependencies['central_redis_client'] # Если нужен здесь

        # УДАЛЕНО: Инициализация TaskQueueCacheManager здесь, т.к. он уже инициализирован и передан
        # self.task_queue_manager = TaskQueueCacheManager(redis_client=central_redis_client_instance)

        self.logger.info("✅ AutoLevelingHandler инициализирован.")

    async def execute(self, payload: Dict[str, Any]) -> None:
        character_ids = payload.get("character_ids", [])
        if not character_ids:
            self.logger.warning("AutoLevelingHandler: получен пустой список ID персонажей. Пропускаем обработку.")
            return

        self.logger.info(f"AutoLevelingHandler: получено {len(character_ids)} ID для обработки.")
        
        # 1. Получаем свой размер батча и имя ARQ-задачи из общих конфигов
        category_name = "auto_leveling"
        
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
                # ИЗМЕНЕНО: Используем self.task_queue_cache_manager
                success = await self.task_queue_cache_manager.add_task_to_queue(
                    batch_id=redis_worker_batch_id,
                    key_template=config.constants.coordinator.TICK_WORKER_BATCH_KEY_TEMPLATE, 
                    specs=batch_data, 
                    target_count=len(batch_data),
                    initial_status="pending"
                )
                
                if success:
                    # ИЗМЕНЕНО: Используем self.arq_redis_client
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
            self.logger.info(f"AutoLevelingHandler: Обработано. Поставлено {successful_batches} батчей задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        elif failed_batches > 0:
            self.logger.error(f"AutoLevelingHandler: Ошибка при обработке. Не удалось поставить ни одного батча задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        else:
            self.logger.info("AutoLevelingHandler: Задачи для обработки не сформированы или батчи пусты.")