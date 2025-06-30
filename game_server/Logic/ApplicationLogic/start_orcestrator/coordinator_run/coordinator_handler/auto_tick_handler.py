# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_run/coordinator_handler/auto_leveling_handler.py

import uuid
from typing import Dict, Any

from arq import ArqRedis

from game_server.config.provider import config
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches
from .base_handler import ICommandHandler

# <<< ИЗМЕНЕНО: Импортируем RedisBatchStore вместо несуществующего интерфейса
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore

class AutoLevelingHandler(ICommandHandler):
    """ Обработчик для команды 'process_auto_leveling'. """

    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        
        # <<< ИЗМЕНЕНО: Извлекаем 'redis_batch_store' вместо 'task_queue_cache_manager'
        # Убедитесь, что в DI-контейнере зависимость зарегистрирована под ключом 'redis_batch_store'
        self.redis_batch_store: RedisBatchStore = dependencies['redis_batch_store']
        self.arq_redis_client: ArqRedis = dependencies['arq_redis_pool']

        self.logger.info("✅ AutoLevelingHandler (v2, RedisBatchStore) инициализирован.")

    async def execute(self, payload: Dict[str, Any]) -> None:
        character_ids = payload.get("character_ids", [])
        if not character_ids:
            self.logger.warning("AutoLevelingHandler: получен пустой список ID персонажей. Пропускаем обработку.")
            return

        self.logger.info(f"AutoLevelingHandler: получено {len(character_ids)} ID для обработки.")
        
        category_name = "auto_leveling"
        
        batch_size = config.settings.runtime.BATCH_SIZES.get(category_name, config.settings.runtime.DEFAULT_BATCH_SIZE)
        arq_task_name = config.constants.coordinator.ARQ_COMMAND_TASK_NAMES.get(category_name)
        
        # <<< ИЗМЕНЕНО: Получаем правильный шаблон ключа для этой задачи.
        # Предполагается, что он есть в конфиге. Если нет, его нужно добавить.
        key_template = config.constants.coordinator.AUTO_LEVELING_BATCH_KEY_TEMPLATE

        if not arq_task_name or not key_template:
            self.logger.error(f"Для категории '{category_name}' не найдено имя ARQ-задачи или шаблон ключа Redis. Пропускаем.")
            return

        instructions = [{"character_id": char_id, "task_type": category_name} for char_id in character_ids]

        successful_batches = 0
        failed_batches = 0
        for batch_instructions in split_into_batches(instructions, batch_size):
            try:
                redis_worker_batch_id = str(uuid.uuid4())
                
                # <<< ИЗМЕНЕНО: Формируем словарь данных для save_batch
                batch_data_to_save = {
                    "specs": batch_instructions,
                    "target_count": len(batch_instructions),
                    "status": "pending"
                }
                
                # <<< ИЗМЕНЕНО: Вызываем self.redis_batch_store.save_batch
                success = await self.redis_batch_store.save_batch(
                    batch_id=redis_worker_batch_id,
                    key_template=key_template,
                    batch_data=batch_data_to_save,
                    ttl_seconds=config.settings.redis.BATCH_TASK_TTL_SECONDS
                )
                
                if success:
                    await self.arq_redis_client.enqueue_job(
                        arq_task_name,  # Позиционный аргумент для имени функции
                        batch_id=redis_worker_batch_id # Именованный аргумент для функции воркера
                    )
                    successful_batches += 1
                    self.logger.debug(f"Задача '{arq_task_name}' с batch_id '{redis_worker_batch_id}' поставлена в очередь ARQ. ({len(batch_instructions)} инструкций)")
                else:
                    failed_batches += 1
                    self.logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' в Redis. ARQ-задача не будет отправлена.")
            except Exception as e:
                failed_batches += 1
                self.logger.error(f"Ошибка при обработке батча для '{category_name}' (инструкций: {len(batch_instructions)}): {e}", exc_info=True)
        
        if successful_batches > 0:
            self.logger.info(f"AutoLevelingHandler: Обработано. Поставлено {successful_batches} батчей задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        elif failed_batches > 0:
            self.logger.error(f"AutoLevelingHandler: Ошибка при обработке. Не удалось поставить ни одного батча задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        else:
            self.logger.info("AutoLevelingHandler: Задачи для обработки не сформированы или батчи пусты.")