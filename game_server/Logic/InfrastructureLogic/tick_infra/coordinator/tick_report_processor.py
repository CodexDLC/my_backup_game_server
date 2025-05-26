import asyncio
import json
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
from game_server.app_cache.redis_client import RedisClient



class ReportProcessor:
    def __init__(self, redis=None, coordinator=None):
        """
        :param redis: Опциональное подключение к Redis
        :param coordinator: Ссылка на родительский Coordinator
        """
        self.redis = redis or RedisClient()
        self.coordinator = coordinator
        self._using_external_redis = redis is not None
        self.db_session = None

    async def __aenter__(self):
        """Контекстный менеджер для безопасного подключения"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Гарантированное освобождение ресурсов"""
        await self.close()

    async def connect(self):
        """Установка соединений с БД"""
        if self.db_session is None:
            self.db_session = await get_db_session().__anext__()
            logger.info("✅ Подключение к БД установлено")

    async def close(self):
        """Корректное закрытие ресурсов"""
        if self.db_session:
            await self.db_session.close()
            self.db_session = None
            
        if not self._using_external_redis:
            await self.redis.close()

    async def process_report(self):
        """Основной метод обработки отчета с улучшенной логикой"""
        try:
            logger.info("🚀 [REPORT] Начало обработки отчета")
            
            async with self:
                batch_data = await self._fetch_batch_data()
                await self._handle_failed_tasks(batch_data)
                await self._update_batch_statuses(batch_data)
                await self._notify_coordinator()
                
            logger.info("🏁 [REPORT] Обработка завершена успешно")
            
        except Exception as e:
            logger.error(f"❌ [REPORT] Критическая ошибка: {str(e)}")
            await self._handle_failure()
            raise

    async def _fetch_batch_data(self) -> dict:
        """Получение данных о батчах"""
        raw_data = await self.redis.hgetall("finish_handlers_tick")
        return {
            batch_id: json.loads(data) 
            for batch_id, data in raw_data.items()
        }

    async def _handle_failed_tasks(self, batch_data: dict):
        """Обработка неудачных задач"""
        for batch_id, data in batch_data.items():
            if data.get("failed_tasks"):
                failed_tasks = json.loads(data["failed_tasks"])
                if failed_tasks:
                    await self.redis.sadd("tick_processing_failed", *failed_tasks)
                    await self.redis.hset("batch_status", batch_id, "failed")
                    logger.warning(f"⚠️ Обнаружены failed-задачи: {failed_tasks}")

    async def _update_batch_statuses(self, batch_data: dict):
        """Обновление статусов батчей"""
        updates = [
            self.redis.hset("batch_status", batch_id, data["status"])
            for batch_id, data in batch_data.items()
        ]
        await asyncio.gather(*updates)
        logger.info(f"🔄 Обновлены статусы для {len(updates)} батчей")

    async def _notify_coordinator(self):
        """Уведомление координатора о завершении"""
        if self.coordinator:
            await self.coordinator.handle_command("clean")
        else:
            await self.redis.publish("coordinator_channel", json.dumps({
                "command": "clean",
                "source": "report_processor"
            }))
        logger.info("📢 Координатор уведомлен о завершении")

    async def _handle_failure(self):
        """Обработка сбоев в процессе"""
        if self.coordinator:
            await self.coordinator.handle_command("process_failed")
        else:
            await self.redis.publish("coordinator_channel", "process_failed")