import asyncio
import json
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.handler.Clean_Processor_handler import (
    cleanup_available_workers, 
    cleanup_batch_results, 
    cleanup_batch_status,
    cleanup_processed_batches, 
    cleanup_successful_handlers, 
    cleanup_tick_processed, 
    cleanup_tick_status,  # ✅ Добавляем корректный импорт
    extract_active_handlers, 
    process_batch_report
)
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger  # Импортируем логгер

from game_server.app_cache.redis_client import RedisClient  
from game_server.Logic.DataAccessLogic.db_instance import get_db_session  


class CleanProcessor:
    def __init__(self):
        self.redis_client = RedisClient()  # ✅ Используем `self.redis_client`
        self.db_session = None

    async def connect(self):
        self.db_session = await get_db_session().__anext__()
        logger.info("✅ Подключение к базе данных установлено!")

    async def cleanup(self):
        """Глобальная очистка старых данных в Redis и завершённых задач."""
        logger.info("🚀 Запуск полного процесса очистки...")

        # ✅ 1. Извлекаем `active_handlers`
        batch_ids, handler_names, statuses = await extract_active_handlers(self.redis_client)

        # ✅ 2. Обрабатываем `finish_handlers_tick`
        batch_status_list, failed_tasks_list = await process_batch_report(self.redis_client)

        # ✅ 3. Чистим `active_handlers`, удаляя `batch_id`, имеющий статус `"success"`
        await cleanup_successful_handlers(self.redis_client, batch_status_list, batch_ids)

        # ✅ 4. Чистим `available_workers_archive`
        await cleanup_available_workers(self.redis_client, batch_status_list, failed_tasks_list, batch_ids)

        # ✅ 5. Чистим `batch_results`
        await cleanup_batch_results(self.redis_client, batch_status_list, failed_tasks_list, batch_ids)

        # ✅ 6. Чистим `tick_processed`, удаляя `"done"`, соответствующий `"success"`
        await cleanup_tick_processed(self.redis_client, batch_status_list)

        # ✅ 7. **В последнюю очередь** очищаем `processed_batches`, удаляя `"success"`
        await cleanup_processed_batches(self.redis_client, batch_status_list)

        # ✅ 8. **В последнюю очередь** очищаем `batch_status`, удаляя `"success"`
        await cleanup_batch_status(self.redis_client, batch_status_list)

        # ✅ 9. **Завершаем очистку `tick_status`**
        await cleanup_tick_status(self.redis_client)  # ✅ Теперь вызываем правильно

        logger.info("🏁 Полный цикл очистки завершён!")

        # Завершаем процесс
        await self.set_status_coordinator("finish_report", False)
        logger.info("🏁 Очистка завершена!")

    async def set_status_coordinator(self, key: str, value: bool):
        """Обновляет статус координатора в Redis."""
        await self.redis_client.set(key, str(value))
        logger.info(f"✅ Статус '{key}' обновлён: {value}")

async def main():
    cleanup = CleanProcessor()
    await cleanup.connect()
    await cleanup.cleanup()  # ✅ Исправлен вызов `cleanup()` вместо `process_tick_data()`

if __name__ == "__main__":
    asyncio.run(main())


