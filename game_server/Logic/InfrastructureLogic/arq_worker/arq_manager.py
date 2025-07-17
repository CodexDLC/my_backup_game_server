# Файл: game_server/Logic/InfrastructureLogic/arq_worker/arq_manager.py

import logging
import inject
from typing import Any, Dict
from arq.connections import create_pool, RedisSettings
from game_server.config.settings_core import REDIS_CACHE_URL

class ArqQueueService: # <--- Переименовываем для ясности
    """
    Сервис для инкапсуляции логики работы с очередью ARQ.
    """
    @inject.autoparams('logger')
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # Готовим объект настроек один раз. Это эффективно.
        self.redis_settings = RedisSettings.from_dsn(REDIS_CACHE_URL)
        self.logger.info("✨ ArqQueueService инициализирован.")

    async def enqueue_job(self, task_name: str, *args, **kwargs) -> Any:
        """
        Универсальный метод для постановки любой задачи в очередь ARQ.
        """
        job_id = kwargs.get('_job_id') or kwargs.get('job_id')
        self.logger.debug(f"Постановка задачи '{task_name}' (ID: {job_id}) в очередь...")

        try:
            # Вся логика создания пула теперь здесь, в одном месте.
            async with await create_pool(self.redis_settings) as arq_client:
                job = await arq_client.enqueue_job(task_name, *args, **kwargs)
            
            self.logger.info(f"✅ Задача '{task_name}' (ID: {job_id}) успешно поставлена в очередь.")
            return job
        except Exception as e:
            self.logger.error(f"❌ Ошибка при постановке задачи '{task_name}' в очередь: {e}", exc_info=True)
            # Можно либо пробросить исключение дальше, либо вернуть None
            raise