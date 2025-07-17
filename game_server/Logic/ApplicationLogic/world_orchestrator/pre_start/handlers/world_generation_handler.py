# Файл: game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/handlers/world_generation_handler.py

import logging
import inject

# <--- Убрали все лишние импорты arq
from .base_step_handler import IPreStartStepHandler
from game_server.config.provider import config
# <--- Добавили импорт нашего нового сервиса
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService

class WorldGenerationHandler(IPreStartStepHandler):
    """Шаг 3: Запускает задачу генерации карты мира через ARQ."""

    # <--- Теперь он зависит только от логгера и нашего сервиса
    @inject.autoparams('arq_service', 'logger')
    def __init__(self, arq_service: ArqQueueService, logger: logging.Logger):
        self.logger = logger
        self._arq_service = arq_service

    async def execute(self) -> bool:
        self.logger.info("--- ⚙️ Шаг 3: Запуск задачи генерации карты мира (фоновый процесс) ---")
        job_id = "world_map_generation_singleton_job"

        try:
            # Просто вызываем метод нашего сервиса. Код стал чистым и понятным.
            await self._arq_service.enqueue_job(
                config.constants.arq.ARQ_TASK_GENERATE_WORLD_MAP,
                job_id, # <--- Передаем job_id как первый позиционный аргумент для задачи
                _defer_by_seconds=5
                # 🔥 job_id больше не _job_id, а прямой аргумент для generate_world_map_task
            )
            return True
        except Exception as e:
            # Ошибка уже будет залогирована внутри сервиса, но мы можем добавить контекст.
            self.logger.critical(f"🚨 Шаг 3: Критическая ошибка при планировании генерации карты: {e}")
            return False