from contextlib import asynccontextmanager
import os
from datetime import datetime, timezone
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger

from game_server.Logic.InfrastructureLogic.tick_infra.collector.tick_collector_processor import collector_handler
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.task_utils import initialize_server
from game_server.app_cache.redis_client import RedisClient
from game_server.Logic.DataAccessLogic.db_in import AsyncDatabase


class Collector:
    """Коллектор с твоим методом run_collector() и безопасным lifecycle."""
    
    def __init__(self, db_url):
        self.redis_client = None  # Для совместимости с твоим кодом
        self.db = AsyncDatabase(db_url)  # ✅ Инициализируем БД
        self.server_start_time = None
        self._is_initialized = False  # Флаг инициализации
        
    async def start(self):
        """Инициализация (аналог твоего initialize())."""
        self.redis_client = RedisClient()    
        await self.db.connect()  # ✅ Подключаем БД        
        self.server_start_time = datetime.now(timezone.utc)
        await self.redis_client.set("collector_status", "active")
        self._is_initialized = True
        logger.info("✅ Collector инициализирован (status=active)")

    async def stop(self):
        """Аналог твоего _safe_shutdown()."""
        if self.db:
            await self.db.disconnect()
        if self.redis_client:
            await self.redis_client.close()
        self._is_initialized = False

    @asynccontextmanager
    async def lifecycle(self):
        """Безопасный контекст (вызов start/stop автоматически)."""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()

    async def run_collector(self, tick_id: str) -> bool:
        """Твой оригинальный метод без изменений."""
        if not self._is_initialized:
            logger.error("Collector не инициализирован!")
            return False

        logger.debug(f"🚀 Запуск сбора данных для tick_id={tick_id}")
        
        try:
            current_time = datetime.now(timezone.utc)
            logger.debug(f"🕒 Время старта: {self.server_start_time}, текущее: {current_time.isoformat()}")
            
            # Основная логика (не трогаем)
            await collector_handler(self.redis_client, tick_id, self.db)
            
            # Уведомляем координатора
            await self.redis_client.publish(
                os.getenv("REDIS_COORDINATOR_CHANNEL", "coordinator_channel"),
                "new_tasks"
            )
            
            await self.redis_client.set("collector_status", "sleep")
            logger.info(f"✅ Сбор данных для tick_id={tick_id} завершен. Status=sleep")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в run_collector: {e}", exc_info=True)
            await self.redis_client.set("collector_status", "error")
            return False