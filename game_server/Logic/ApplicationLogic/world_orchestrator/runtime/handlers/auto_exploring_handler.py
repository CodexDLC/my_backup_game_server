# game_server/Logic/ApplicationLogic/world_orchestrator/runtime/handlers/auto_exploring_handler.py

import uuid
from typing import Dict, Any
import logging # Добавлено для типизации логгера
import inject # Добавлено для inject.autoparams

from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService
from game_server.Logic.InfrastructureLogic.arq_worker.utils.task_batch_dispatcher import split_into_batches
from game_server.config.provider import config
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from .base_command_handler import ICommandHandler


class AutoExploringHandler(ICommandHandler):
    """ Обработчик для команды 'process_auto_exploring'. """

    # 🔥 ИЗМЕНЕНИЕ: Используем inject.autoparams для автоматического внедрения зависимостей
    @inject.autoparams('redis_batch_store', 'arq_service')
    def __init__(
        self,
        redis_batch_store: RedisBatchStore,
        arq_service: ArqQueueService,
        # logger: logging.Logger # Логгер будет получен из базового класса через inject.attr
    ):
        # super().__init__(dependencies) # 🔥 УДАЛЕНО: Больше не передаем dependencies в базовый класс

        self.redis_batch_store = redis_batch_store
        self.arq_service = arq_service

        self.logger.info("✅ AutoExploringHandler (v2, RedisBatchStore) инициализирован.")

    async def execute(self, payload: Dict[str, Any]) -> None:
        character_ids = payload.get("character_ids", [])
        if not character_ids:
            self.logger.warning("AutoExploringHandler: получен пустой список ID персонажей. Пропускаем обработку.")
            return

        self.logger.info(f"AutoExploringHandler: получено {len(character_ids)} ID для обработки.")

        category_name = "auto_exploring"

        batch_size = config.settings.runtime.BATCH_SIZES.get(category_name, config.settings.runtime.DEFAULT_BATCH_SIZE)
        arq_task_name = config.constants.coordinator.ARQ_COMMAND_TASK_NAMES.get(category_name)

        key_template = config.constants.coordinator.AUTO_EXPLORING_BATCH_KEY_TEMPLATE

        if not arq_task_name or not key_template:
            self.logger.error(f"Для категории '{category_name}' не найдено имя ARQ-задачи или шаблон ключа Redis. Пропускаем.")
            return

        instructions = [{"character_id": char_id, "task_type": category_name} for char_id in character_ids]

        successful_batches = 0
        failed_batches = 0
        for batch_instructions in split_into_batches(instructions, batch_size):
            try:
                redis_worker_batch_id = str(uuid.uuid4())

                batch_data_to_save = {
                    "specs": batch_instructions,
                    "target_count": len(batch_instructions),
                    "status": "pending"
                }

                success = await self.redis_batch_store.save_batch(
                    batch_id=redis_worker_batch_id,
                    key_template=key_template,
                    batch_data=batch_data_to_save,
                    ttl_seconds=config.settings.redis.BATCH_TASK_TTL_SECONDS
                )

                if success:
                    await self.arq_service.enqueue_job(
                        arq_task_name,
                        batch_id=redis_worker_batch_id
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
            self.logger.info(f"AutoExploringHandler: Обработано. Поставлено {successful_batches} батчей задач '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        elif failed_batches > 0:
            self.logger.error(f"AutoExploringHandler: Ошибка при обработке. Не удалось поставить ни одного батча '{arq_task_name}' в очередь. Ошибок: {failed_batches}.")
        else:
            self.logger.info("AutoExploringHandler: Задачи для обработки не сформированы или батчи пусты.")